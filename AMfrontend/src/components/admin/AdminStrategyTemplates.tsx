import { useState, useEffect } from "react";
import { Button } from "../ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import {
  fetchStrategyTemplates,
  updateTemplateParams,
  type StrategyTemplate,
} from "../../lib/adminApi";

export function AdminStrategyTemplates() {
  const [templates, setTemplates] = useState<StrategyTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Settings modal state
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<StrategyTemplate | null>(null);
  const [rebalancePeriod, setRebalancePeriod] = useState<string>("");
  const [settingsSaving, setSettingsSaving] = useState(false);

  useEffect(() => {
    loadTemplates();
  }, []);

  async function loadTemplates() {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchStrategyTemplates();
      setTemplates(data.templates);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load templates';
      setError(errorMessage);
      console.error('Failed to load templates:', err);
    } finally {
      setLoading(false);
    }
  }

  function handleOpenSettings(template: StrategyTemplate) {
    setSelectedTemplate(template);
    setRebalancePeriod(template.rebalance_period_minutes.toString());
    setSettingsOpen(true);
  }

  async function handleSaveSettings() {
    if (!selectedTemplate) return;

    const periodMinutes = parseInt(rebalancePeriod, 10);

    if (isNaN(periodMinutes) || periodMinutes < 1 || periodMinutes > 1440) {
      alert('Rebalance period must be between 1 and 1440 minutes');
      return;
    }

    try {
      setSettingsSaving(true);

      console.log('[TEMPLATE] Saving template settings:', {
        templateId: selectedTemplate.id,
        rebalancePeriodMinutes: periodMinutes,
      });

      const result = await updateTemplateParams(
        selectedTemplate.id,
        periodMinutes
      );

      console.log('[TEMPLATE] Save result:', result);

      setSettingsOpen(false);
      await loadTemplates();

      alert('Strategy template settings updated successfully!');
    } catch (err: any) {
      let errorMessage = 'Failed to update settings';

      if (err.response?.data?.detail) {
        errorMessage = typeof err.response.data.detail === 'string'
          ? err.response.data.detail
          : JSON.stringify(err.response.data.detail);
      } else if (err.response?.data?.message) {
        errorMessage = err.response.data.message;
      } else if (err.message) {
        errorMessage = err.message;
      }

      alert(`Error: ${errorMessage}`);
      console.error('Failed to update settings:', err);
    } finally {
      setSettingsSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-slate-400">Loading templates...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-800 bg-red-950/20 p-4">
        <p className="text-sm text-red-400">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-slate-800 bg-slate-950/50">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-800">
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                  Template Name
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                  Rebalance Period
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                  Business Agents
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                  Instances
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {templates.map((template) => (
                <tr key={template.id} className="hover:bg-slate-800/30">
                  <td className="px-4 py-3">
                    <div>
                      <div className="text-sm font-medium text-white">
                        {template.display_name}
                      </div>
                      {template.description && (
                        <div className="text-xs text-slate-400 mt-0.5">
                          {template.description}
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-300">
                    {template.rebalance_period_minutes} min
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-300">
                    {template.business_agents.join(', ')}
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-300">
                    {template.instance_count}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex px-2 py-0.5 text-xs font-medium rounded ${
                        template.is_active
                          ? 'bg-green-900/20 text-green-400'
                          : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      {template.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-xs"
                      onClick={() => handleOpenSettings(template)}
                    >
                      Settings
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Settings Modal */}
      <Dialog open={settingsOpen} onOpenChange={setSettingsOpen}>
        <DialogContent className="sm:max-w-[500px] bg-slate-900 border-slate-800">
          <DialogHeader>
            <DialogTitle className="text-white">
              Strategy Template Settings
            </DialogTitle>
            <DialogDescription className="text-slate-400">
              Configure execution period for {selectedTemplate?.display_name}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="rebalance-period" className="text-white">
                Rebalance Period (minutes)
              </Label>
              <Input
                id="rebalance-period"
                type="number"
                min="1"
                max="1440"
                value={rebalancePeriod}
                onChange={(e) => setRebalancePeriod(e.target.value)}
                className="bg-slate-800 border-slate-700 text-white"
              />
              <p className="text-xs text-slate-400">
                How often strategies using this template execute (1-1440 minutes)
              </p>
              {selectedTemplate && selectedTemplate.instance_count > 0 && (
                <p className="text-xs text-yellow-400">
                  ⚠️ This will affect {selectedTemplate.instance_count} active instance(s)
                </p>
              )}
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setSettingsOpen(false)}
              disabled={settingsSaving}
            >
              Cancel
            </Button>
            <Button onClick={handleSaveSettings} disabled={settingsSaving}>
              {settingsSaving ? 'Saving...' : 'Save Changes'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
