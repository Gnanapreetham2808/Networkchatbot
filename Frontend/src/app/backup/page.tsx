"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Download, RefreshCw, Database, Check, X, Clock, HardDrive } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface Backup {
  device: string;
  host: string;
  timestamp: string;
  status: string;
  json_file: string;
  txt_file: string;
  size_kb: number;
}

interface BackupSummary {
  successful: number;
  failed: number;
  successful_devices: string[];
  failed_devices: string[];
}

export default function BackupPage() {
  const [backups, setBackups] = useState<Backup[]>([]);
  const [devices, setDevices] = useState<any[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<string>("all");
  const [loading, setLoading] = useState(false);
  const [backupInProgress, setBackupInProgress] = useState(false);
  const [summary, setSummary] = useState<BackupSummary | null>(null);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/nlp";

  // Load devices and backups on mount
  useEffect(() => {
    loadDevices();
    loadBackups();
  }, []);

  const loadDevices = async () => {
    try {
      const res = await fetch(`${API_BASE}/devices/`);
      const data = await res.json();
      if (data.devices) {
        setDevices(Object.values(data.devices));
      }
    } catch (error) {
      console.error("Failed to load devices:", error);
    }
  };

  const loadBackups = async (device?: string) => {
    setLoading(true);
    try {
      const url = device && device !== "all" 
        ? `${API_BASE}/backup/?device=${device}`
        : `${API_BASE}/backup/`;
      
      const res = await fetch(url);
      const data = await res.json();
      
      if (data.status === "success") {
        setBackups(data.backups || []);
      }
    } catch (error) {
      console.error("Failed to load backups:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeviceChange = (value: string) => {
    setSelectedDevice(value);
    loadBackups(value === "all" ? undefined : value);
  };

  const startBackup = async (deviceAlias?: string) => {
    setBackupInProgress(true);
    setSummary(null);
    
    try {
      const payload = deviceAlias 
        ? { device: deviceAlias }
        : { backup_all: true };
      
      const res = await fetch(`${API_BASE}/backup/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      
      const data = await res.json();
      
      if (data.status === "success") {
        if (data.summary) {
          setSummary(data.summary);
        }
        await loadBackups(selectedDevice === "all" ? undefined : selectedDevice);
      } else {
        alert(`Backup failed: ${data.error || "Unknown error"}`);
      }
    } catch (error) {
      console.error("Backup failed:", error);
      alert("Failed to create backup");
    } finally {
      setBackupInProgress(false);
    }
  };

  const downloadFile = (filepath: string) => {
    // Create download link (file should be served by backend)
    const filename = filepath.split(/[\\\/]/).pop();
    window.open(`${API_BASE}/backup/download/${filename}`, "_blank");
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleString();
    } catch {
      return timestamp;
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold mb-2">Device Configuration Backup</h1>
        <p className="text-muted-foreground">
          Manage and download device configuration backups
        </p>
      </div>

      {/* Backup Controls */}
      <Card>
        <CardHeader>
          <CardTitle>Create Backup</CardTitle>
          <CardDescription>
            Backup device configurations to JSON and TXT formats
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-4 items-end">
            <div className="flex-1">
              <label className="text-sm font-medium mb-2 block">Select Device</label>
              <Select value={selectedDevice} onValueChange={handleDeviceChange}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a device" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Devices</SelectItem>
                  {devices.map((device) => (
                    <SelectItem key={device.alias} value={device.alias}>
                      {device.alias} ({device.host})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <Button
              onClick={() => startBackup(selectedDevice === "all" ? undefined : selectedDevice)}
              disabled={backupInProgress}
              className="gap-2"
            >
              {backupInProgress ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  Backing up...
                </>
              ) : (
                <>
                  <Database className="h-4 w-4" />
                  Create Backup
                </>
              )}
            </Button>
            
            <Button
              variant="outline"
              onClick={() => loadBackups(selectedDevice === "all" ? undefined : selectedDevice)}
              disabled={loading}
              className="gap-2"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          </div>

          {/* Backup Summary */}
          {summary && (
            <div className="mt-4 p-4 border rounded-lg bg-muted/50">
              <h3 className="font-semibold mb-3">Backup Summary</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-600" />
                  <span>Successful: {summary.successful}</span>
                </div>
                <div className="flex items-center gap-2">
                  <X className="h-4 w-4 text-red-600" />
                  <span>Failed: {summary.failed}</span>
                </div>
              </div>
              {summary.failed > 0 && (
                <div className="mt-2">
                  <p className="text-sm text-muted-foreground">
                    Failed devices: {summary.failed_devices.join(", ")}
                  </p>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Backups List */}
      <Card>
        <CardHeader>
          <CardTitle>Backup History</CardTitle>
          <CardDescription>
            {backups.length} backup{backups.length !== 1 ? "s" : ""} found
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-20 w-full" />
              ))}
            </div>
          ) : backups.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <HardDrive className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No backups found</p>
              <p className="text-sm mt-1">Create your first backup to get started</p>
            </div>
          ) : (
            <div className="space-y-3">
              {backups.map((backup, index) => (
                <div
                  key={index}
                  className="border rounded-lg p-4 hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="space-y-1 flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold">{backup.device}</h3>
                        <Badge
                          variant={backup.status === "success" ? "default" : "destructive"}
                        >
                          {backup.status}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">{backup.host}</p>
                      <div className="flex items-center gap-4 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {formatTimestamp(backup.timestamp)}
                        </span>
                        <span>{backup.size_kb.toFixed(2)} KB</span>
                      </div>
                    </div>
                    
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => downloadFile(backup.json_file)}
                        className="gap-2"
                      >
                        <Download className="h-4 w-4" />
                        JSON
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => downloadFile(backup.txt_file)}
                        className="gap-2"
                      >
                        <Download className="h-4 w-4" />
                        TXT
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
