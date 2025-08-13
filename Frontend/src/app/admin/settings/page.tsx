'use client';
import { FiSave, FiSliders, FiBell, FiShield, FiUser } from 'react-icons/fi';
import { useState } from 'react';

export default function SettingsPage() {
  const [settings, setSettings] = useState({
    darkMode: false,
    notifications: true,
    commandConfirmation: true,
    sessionTimeout: 30,
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, type, checked, value } = e.target;
    setSettings(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSave = () => {
    alert('Settings saved successfully!');
    // You can replace this with actual save logic (API call etc.)
  };

  return (
    <main className="max-w-4xl mx-auto py-12 px-4 sm:px-6 lg:px-8 text-gray-800">
      <h2 className="text-3xl font-bold mb-8 flex items-center gap-2">
        <FiSliders className="text-blue-600" /> Settings
      </h2>

      <div className="space-y-8">
        {/* Theme Settings */}
        <div className="bg-white rounded-xl shadow p-6 border border-gray-100">
          <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <FiUser /> Appearance
          </h3>
          <div className="flex items-center justify-between">
            <label className="font-medium">Enable Dark Mode</label>
            <input
              type="checkbox"
              name="darkMode"
              checked={settings.darkMode}
              onChange={handleChange}
              className="w-5 h-5 text-blue-600 rounded"
            />
          </div>
        </div>

        {/* Notifications */}
        <div className="bg-white rounded-xl shadow p-6 border border-gray-100">
          <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <FiBell /> Notifications
          </h3>
          <div className="flex items-center justify-between">
            <label className="font-medium">Receive Alerts</label>
            <input
              type="checkbox"
              name="notifications"
              checked={settings.notifications}
              onChange={handleChange}
              className="w-5 h-5 text-blue-600 rounded"
            />
          </div>
        </div>

        {/* Security */}
        <div className="bg-white rounded-xl shadow p-6 border border-gray-100">
          <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <FiShield /> Security
          </h3>
          <div className="flex items-center justify-between mb-4">
            <label className="font-medium">Command Confirmation</label>
            <input
              type="checkbox"
              name="commandConfirmation"
              checked={settings.commandConfirmation}
              onChange={handleChange}
              className="w-5 h-5 text-blue-600 rounded"
            />
          </div>

          <div className="flex items-center justify-between">
            <label className="font-medium">
              Session Timeout <span className="text-sm text-gray-500">(min)</span>
            </label>
            <input
              type="range"
              name="sessionTimeout"
              min={5}
              max={120}
              step={5}
              value={settings.sessionTimeout}
              onChange={handleChange}
              className="w-2/3"
            />
            <span className="ml-2 text-sm text-gray-700">{settings.sessionTimeout} min</span>
          </div>
        </div>

        {/* Save Button */}
        <div className="text-right">
          <button
            onClick={handleSave}
            className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium transition-colors"
          >
            <FiSave /> Save Settings
          </button>
        </div>
      </div>
    </main>
  );
}
