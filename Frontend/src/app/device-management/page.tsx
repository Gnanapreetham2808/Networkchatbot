"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Plus, Server, Trash2, Edit } from "lucide-react";

interface Device {
  alias: string;
  host: string;
  username: string;
  password: string;
  device_type: string;
  vendor: string;
  model?: string;
  location?: string;
  role?: string;
}

export default function DeviceManagementPage() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [formData, setFormData] = useState<Partial<Device>>({
    device_type: "cisco_ios",
    vendor: "cisco",
    role: "access",
  });

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/nlp";

  useEffect(() => {
    loadDevices();
  }, []);

  const loadDevices = async () => {
    try {
      const res = await fetch(`${API_BASE}/device-management/`);
      const data = await res.json();
      if (data.status === "success") {
        setDevices(Object.values(data.devices));
      }
    } catch (error) {
      console.error("Failed to load devices:", error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const res = await fetch(`${API_BASE}/device-management/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });
      
      const data = await res.json();
      
      if (data.status === "success") {
        alert("Device added successfully!");
        setIsDialogOpen(false);
        setFormData({
          device_type: "cisco_ios",
          vendor: "cisco",
          role: "access",
        });
        loadDevices();
      } else {
        alert(`Error: ${data.error}`);
      }
    } catch (error) {
      console.error("Failed to add device:", error);
      alert("Failed to add device");
    }
  };

  const handleInputChange = (field: keyof Device, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2">Device Management</h1>
          <p className="text-muted-foreground">
            Configure and manage network devices
          </p>
        </div>
        
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button className="gap-2">
              <Plus className="h-4 w-4" />
              Add Device
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Add New Device</DialogTitle>
              <DialogDescription>
                Configure a new network device with connection details
              </DialogDescription>
            </DialogHeader>
            
            <form onSubmit={handleSubmit}>
              <div className="grid grid-cols-2 gap-4 py-4">
                {/* Alias */}
                <div className="space-y-2">
                  <Label htmlFor="alias">Device Alias *</Label>
                  <Input
                    id="alias"
                    placeholder="e.g., CORE-SW-01"
                    value={formData.alias || ""}
                    onChange={(e) => handleInputChange("alias", e.target.value)}
                    required
                  />
                </div>
                
                {/* Host/IP */}
                <div className="space-y-2">
                  <Label htmlFor="host">IP Address *</Label>
                  <Input
                    id="host"
                    placeholder="e.g., 192.168.1.1"
                    value={formData.host || ""}
                    onChange={(e) => handleInputChange("host", e.target.value)}
                    required
                  />
                </div>
                
                {/* Username */}
                <div className="space-y-2">
                  <Label htmlFor="username">Username *</Label>
                  <Input
                    id="username"
                    placeholder="admin"
                    value={formData.username || ""}
                    onChange={(e) => handleInputChange("username", e.target.value)}
                    required
                  />
                </div>
                
                {/* Password */}
                <div className="space-y-2">
                  <Label htmlFor="password">Password *</Label>
                  <Input
                    id="password"
                    type="password"
                    placeholder="••••••••"
                    value={formData.password || ""}
                    onChange={(e) => handleInputChange("password", e.target.value)}
                    required
                  />
                </div>
                
                {/* Vendor */}
                <div className="space-y-2">
                  <Label htmlFor="vendor">Vendor</Label>
                  <Select
                    value={formData.vendor}
                    onValueChange={(value) => handleInputChange("vendor", value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="cisco">Cisco</SelectItem>
                      <SelectItem value="aruba">Aruba</SelectItem>
                      <SelectItem value="juniper">Juniper</SelectItem>
                      <SelectItem value="hp">HPE</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                {/* Device Type */}
                <div className="space-y-2">
                  <Label htmlFor="device_type">Device Type</Label>
                  <Select
                    value={formData.device_type}
                    onValueChange={(value) => handleInputChange("device_type", value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="cisco_ios">Cisco IOS</SelectItem>
                      <SelectItem value="cisco_xe">Cisco IOS-XE</SelectItem>
                      <SelectItem value="aruba_aoscx">Aruba AOS-CX</SelectItem>
                      <SelectItem value="aruba_os">Aruba ProVision</SelectItem>
                      <SelectItem value="juniper_junos">Juniper JunOS</SelectItem>
                      <SelectItem value="hp_comware">HPE Comware</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                {/* Model */}
                <div className="space-y-2">
                  <Label htmlFor="model">Model</Label>
                  <Input
                    id="model"
                    placeholder="e.g., WS-C3650-24TS"
                    value={formData.model || ""}
                    onChange={(e) => handleInputChange("model", e.target.value)}
                  />
                </div>
                
                {/* Location */}
                <div className="space-y-2">
                  <Label htmlFor="location">Location</Label>
                  <Input
                    id="location"
                    placeholder="e.g., London DC"
                    value={formData.location || ""}
                    onChange={(e) => handleInputChange("location", e.target.value)}
                  />
                </div>
                
                {/* Role */}
                <div className="space-y-2">
                  <Label htmlFor="role">Role</Label>
                  <Select
                    value={formData.role}
                    onValueChange={(value) => handleInputChange("role", value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="core">Core</SelectItem>
                      <SelectItem value="distribution">Distribution</SelectItem>
                      <SelectItem value="access">Access</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setIsDialogOpen(false)}
                >
                  Cancel
                </Button>
                <Button type="submit">Add Device</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Devices List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {devices.map((device) => (
          <Card key={device.alias} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <Server className="h-5 w-5 text-primary" />
                  <CardTitle className="text-lg">{device.alias}</CardTitle>
                </div>
                <Badge variant="outline">{device.role || "access"}</Badge>
              </div>
              <CardDescription>{device.host}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="text-sm space-y-1">
                <p>
                  <span className="font-medium">Vendor:</span> {device.vendor}
                </p>
                <p>
                  <span className="font-medium">Type:</span> {device.device_type}
                </p>
                {device.model && (
                  <p>
                    <span className="font-medium">Model:</span> {device.model}
                  </p>
                )}
                {device.location && (
                  <p>
                    <span className="font-medium">Location:</span> {device.location}
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {devices.length === 0 && (
        <Card>
          <CardContent className="text-center py-12">
            <Server className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p className="text-muted-foreground">No devices configured</p>
            <p className="text-sm text-muted-foreground mt-1">
              Add your first device to get started
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
