import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { AddHoursDialog } from '@/components/goals/AddHoursDialog';
import { WorkEntryList } from '@/components/goals/WorkEntryList';
import { Goal } from '@/types/goal';
import { GoalsAPI } from '@/lib/goals-api';
import { EntriesAPI } from '@/lib/entries-api';
import { generateGoalPDF } from '@/lib/pdf-api';
import { MailerAPI } from '@/lib/mailer-api';
import { useAuth } from '@/context/AuthContext';
import { useUserController } from '@/controllers/useUserController';
import { getCurrencySymbol } from '@/lib/utils';
import {
  ArrowLeft,
  Plus,
  FileDown,
  Clock,
  DollarSign,
  Calendar,
  Settings,
  Mail,
  Save,
  Loader,
  Send,
} from 'lucide-react';
import { format } from 'date-fns';
import { toast } from 'sonner';

export default function GoalDetail() {
  const { id } = useParams<{ id: string }>();
  const { token } = useAuth();
  const { user } = useUserController();
  
  const [goal, setGoal] = useState<Goal | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [addHoursOpen, setAddHoursOpen] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);

  // Pagination and sorting state
  const [entriesPage, setEntriesPage] = useState(1);
  const [entriesPerPage] = useState(5);
  const [totalEntries, setTotalEntries] = useState(0);
  const [sortBy, setSortBy] = useState<'work_date' | 'minutes'>('work_date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Settings form state
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [targetHours, setTargetHours] = useState('0');
  const [hourlyRate, setHourlyRate] = useState('0');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  // Email settings state
  const [emailEnabled, setEmailEnabled] = useState(false);
  const [emailRecipient, setEmailRecipient] = useState('');
  const [emailSendDay, setEmailSendDay] = useState<number>(1);
  const [isSendingNow, setIsSendingNow] = useState(false);
  const [emailSettingsLoaded, setEmailSettingsLoaded] = useState(false);

  // Fetch goal and entries data
  useEffect(() => {
    const fetchGoal = async () => {
      console.log('fetchGoal running - id:', id, 'token:', token ? 'exists' : 'missing');
      if (!id || !token) {
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        console.log('Fetching goal data...');
        const goalData = await GoalsAPI.getGoal(id, token);
        const entriesData = await EntriesAPI.listGoalEntries(id, 0, entriesPerPage, token, sortBy, sortOrder);
        
        // Calculate completed hours from entries
        const completedMinutes = entriesData.entries.reduce((sum, entry) => sum + Number(entry.minutes || 0), 0);
        const completedHours = completedMinutes / 60;
        
        const goalWithEntries: Goal = {
          ...goalData,
          completedHours,
          workEntries: entriesData.entries || [],
        };
        
        setGoal(goalWithEntries);
        setTotalEntries(entriesData.total);
        setEntriesPage(1);
        
        // Update form state
        setName(goalWithEntries.name);
        setDescription(goalWithEntries.description);
        setTargetHours(String(goalWithEntries.targetHours));
        setHourlyRate(String(goalWithEntries.hourlyRate));
        setStartDate(goalWithEntries.startDate);
        setEndDate(goalWithEntries.endDate);
        
        // Fetch email settings
        try {
          const emailSettings = await MailerAPI.getEmailSettings(id, token);
          console.log('Email settings loaded:', emailSettings);
          setEmailEnabled(emailSettings.enabled);
          setEmailRecipient(emailSettings.recipient);
          setEmailSendDay(emailSettings.sent_when);
          setEmailSettingsLoaded(true);
        } catch (err) {
          // Email settings not configured yet - reset to defaults
          console.log('Email settings not configured yet:', err);
          setEmailEnabled(false);
          setEmailRecipient('');
          setEmailSendDay(1);
          setEmailSettingsLoaded(false);
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to load goal';
        console.error('Failed to fetch goal:', err);
        toast.error(errorMessage);
      } finally {
        setIsLoading(false);
      }
    };

    fetchGoal();
  }, [id, token, sortBy, sortOrder]);

  const handleAddHours = async (entry: {
    date: string;
    startTime: string;
    endTime: string;
    minutes: number;
    description: string;
  }) => {
    if (!goal || !token) return;

    try {
      setIsSaving(true);
      
      const entryData = {
        goal_id: goal.id,
        date: entry.date,
        startTime: entry.startTime,
        endTime: entry.endTime,
        description: entry.description,
      };
      
      const newEntry = await EntriesAPI.createEntry(entryData, token);
      
      // Reload entries with current sort settings
      const entriesData = await EntriesAPI.listGoalEntries(id!, 0, entriesPage * entriesPerPage, token, sortBy, sortOrder);
      
      // Recalculate completed hours from all entries
      const totalMinutes = entriesData.entries.reduce((sum, e) => sum + Number(e.minutes || 0), 0);
      const completedHours = totalMinutes / 60;
      
      // Update goal with recalculated hours
      const updatedGoal = {
        ...goal,
        completedHours: Math.round(completedHours * 100) / 100,
        workEntries: entriesData.entries,
      };
      
      setGoal(updatedGoal);
      setTotalEntries(entriesData.total);
      
      setAddHoursOpen(false);
      toast.success('Hours logged successfully');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to add hours';
      toast.error(errorMessage);
      console.error('Failed to add hours:', err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleLoadMore = async () => {
    if (!goal || !token || !id) return;

    try {
      setIsLoadingMore(true);
      const nextPage = entriesPage + 1;
      const skip = (nextPage - 1) * entriesPerPage;
      
      const entriesData = await EntriesAPI.listGoalEntries(id, skip, entriesPerPage, token, sortBy, sortOrder);
      
      // Append new entries to existing ones
      const updatedGoal = {
        ...goal,
        workEntries: [...goal.workEntries, ...entriesData.entries],
      };
      
      setGoal(updatedGoal);
      setEntriesPage(nextPage);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load more entries';
      toast.error(errorMessage);
      console.error('Failed to load more entries:', err);
    } finally {
      setIsLoadingMore(false);
    }
  };

  const handleSortChange = (newSortBy: 'work_date' | 'minutes') => {
    if (newSortBy === sortBy) {
      // Toggle sort order if clicking the same sort field
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(newSortBy);
      setSortOrder('desc');
    }
  };

  const handleGeneratePDF = async () => {
    if (!goal || !token) return;
    
    try {
      await generateGoalPDF(goal.id, token);
      toast.success('PDF report generated and downloaded');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to generate PDF';
      toast.error(errorMessage);
    }
  };

  const handleSaveSettings = async () => {
    if (!goal || !token) return;

    try {
      setIsSaving(true);
      const updated = await GoalsAPI.updateGoal(
        goal.id,
        {
          name,
          description,
          targetHours: parseFloat(targetHours),
          hourlyRate: parseFloat(hourlyRate),
          startDate,
          endDate,
        },
        token
      );
      
      setGoal({
        ...updated,
        workEntries: goal.workEntries,
      });
      
      toast.success('Goal settings saved');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save settings';
      toast.error(errorMessage);
      console.error('Failed to save settings:', err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveEmailSettings = async (newEnabled?: boolean, newRecipient?: string, newSendDay?: number) => {
    if (!goal || !token) return;
    
    // Use provided values or current state
    const enabled = newEnabled !== undefined ? newEnabled : emailEnabled;
    const recipient = newRecipient !== undefined ? newRecipient : emailRecipient;
    const sendDay = newSendDay !== undefined ? newSendDay : emailSendDay;
    
    if (enabled && !recipient) {
      toast.error('Please enter a recipient email address');
      return;
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (enabled && !emailRegex.test(recipient)) {
      toast.error('Please enter a valid email address');
      return;
    }

    try {
      setIsSaving(true);
      
      const settingsData = {
        goal_id: goal.id,
        recipient_email: recipient,
        enabled: enabled,
        send_day: sendDay,
      };

      const savedSettings = await MailerAPI.saveEmailSettings(settingsData, token);
      
      // Update local state with the saved settings
      setEmailEnabled(savedSettings.enabled);
      setEmailRecipient(savedSettings.recipient);
      setEmailSendDay(savedSettings.sent_when);
      setEmailSettingsLoaded(true);
      
      toast.success('Email settings saved successfully');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save email settings';
      toast.error(errorMessage);
      console.error('Failed to save email settings:', err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleEmailEnabledChange = async (checked: boolean) => {
    setEmailEnabled(checked);
    if (emailSettingsLoaded) {
      // Auto-save when settings already exist
      await handleSaveEmailSettings(checked);
    }
  };

  const handleEmailRecipientBlur = async () => {
    if (emailSettingsLoaded && emailRecipient) {
      await handleSaveEmailSettings();
    }
  };

  const handleEmailSendDayChange = async (day: string) => {
    const dayNum = Number(day);
    setEmailSendDay(dayNum);
    if (emailSettingsLoaded) {
      await handleSaveEmailSettings(undefined, undefined, dayNum);
    }
  };

  const handleSendNow = async () => {
    if (!goal || !token) return;

    if (!emailSettingsLoaded) {
      toast.error('Please configure and save email settings first');
      return;
    }

    try {
      setIsSendingNow(true);
      const result = await MailerAPI.sendNow(goal.id, token);
      toast.success(result.message);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send email';
      toast.error(errorMessage);
      console.error('Failed to send email:', err);
    } finally {
      setIsSendingNow(false);
    }
  };

  if (isLoading) {
    return (
      <div className="container py-8">
        <div className="text-center py-16">
          <Loader className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading goal details...</p>
        </div>
      </div>
    );
  }

  if (!goal) {
    return (
      <div className="container py-8">
        <div className="text-center py-16">
          <h2 className="text-xl font-semibold mb-2">Goal not found</h2>
          <p className="text-muted-foreground mb-4">This goal doesn't exist or has been deleted.</p>
          <Button asChild>
            <Link to="/dashboard">Back to Dashboard</Link>
          </Button>
        </div>
      </div>
    );
  }

  const progressPercent = Math.min((goal.completedHours / goal.targetHours) * 100, 100);
  const isCompleted = progressPercent >= 100;
  const earnedAmount = goal.completedHours * goal.hourlyRate;
  const currencySymbol = getCurrencySymbol(user?.currency);

  return (
    <div className="container py-8 max-w-5xl">
      {/* Header */}
      <div className="mb-8 animate-fade-in">
        <Button variant="ghost" size="sm" asChild className="mb-4 -ml-2">
          <Link to="/dashboard">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Dashboard
          </Link>
        </Button>

        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-2xl font-bold tracking-tight">{goal.name}</h1>
              <Badge variant={isCompleted ? "default" : "secondary"} className={isCompleted ? "bg-money" : ""}>
                {isCompleted ? 'Completed' : 'In Progress'}
              </Badge>
            </div>
            <p className="text-muted-foreground">{goal.description}</p>
          </div>

          <div className="flex gap-2">
            <Button variant="outline" onClick={handleGeneratePDF}>
              <FileDown className="h-4 w-4 mr-2" />
              Export PDF
            </Button>
            <Button onClick={() => setAddHoursOpen(true)} disabled={isSaving}>
              <Plus className="h-4 w-4 mr-2" />
              Log Hours
            </Button>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4 mb-8">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <Clock className="h-4 w-4" />
              <span className="text-sm">Hours</span>
            </div>
            <p className="text-2xl font-bold">
              {goal.completedHours.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} / {goal.targetHours.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} h
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <DollarSign className="h-4 w-4" />
              <span className="text-sm">Earned</span>
            </div>
            <p className="text-2xl font-bold text-money">
              {currencySymbol} {earnedAmount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <DollarSign className="h-4 w-4" />
              <span className="text-sm">Rate</span>
            </div>
            <p className="text-2xl font-bold">{currencySymbol} {goal.hourlyRate.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} / h</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <Calendar className="h-4 w-4" />
              <span className="text-sm">Deadline</span>
            </div>
            <p className="text-2xl font-bold">
              {format(new Date(goal.endDate), 'dd MMM yyyy')}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Progress */}
      <Card className="mb-8">
        <CardContent className="pt-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Overall Progress</span>
            <span className="text-sm font-medium">{progressPercent.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%</span>
          </div>
          <Progress value={progressPercent} className="h-3" />
        </CardContent>
      </Card>

      {/* Tabs */}
      <Tabs defaultValue="entries" className="space-y-6">
        <TabsList>
          <TabsTrigger value="entries">Work Entries</TabsTrigger>
          <TabsTrigger value="settings">Goal Settings</TabsTrigger>
          <TabsTrigger value="email">Email Settings</TabsTrigger>
        </TabsList>

        <TabsContent value="entries" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <CardTitle>Work Log</CardTitle>
                  <CardDescription>
                    All hours logged for this goal ({totalEntries} total)
                  </CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant={sortBy === 'work_date' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => handleSortChange('work_date')}
                  >
                    Date {sortBy === 'work_date' && (sortOrder === 'asc' ? '↑' : '↓')}
                  </Button>
                  <Button
                    variant={sortBy === 'minutes' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => handleSortChange('minutes')}
                  >
                    Duration {sortBy === 'minutes' && (sortOrder === 'asc' ? '↑' : '↓')}
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <WorkEntryList entries={goal.workEntries} hourlyRate={goal.hourlyRate} currency={user?.currency} />
              
              {goal.workEntries.length < totalEntries && (
                <div className="mt-4 text-center">
                  <Button
                    variant="outline"
                    onClick={handleLoadMore}
                    disabled={isLoadingMore}
                  >
                    {isLoadingMore ? (
                      <>
                        <Loader className="h-4 w-4 mr-2 animate-spin" />
                        Loading...
                      </>
                    ) : (
                      <>Load More ({totalEntries - goal.workEntries.length} remaining)</>
                    )}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="settings" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Goal Settings
              </CardTitle>
              <CardDescription>
                Configure your goal parameters
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="goal-name">Goal Name</Label>
                  <Input
                    id="goal-name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="start-date">Target Start Date</Label>
                  <Input
                    id="start-date"
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="end-date">Target End Date</Label>
                  <Input
                    id="end-date"
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="goal-desc">Description</Label>
                <Textarea
                  id="goal-desc"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={3}
                />
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="target-hours">Target Hours</Label>
                  <Input
                    id="target-hours"
                    type="number"
                    min="1"
                    value={targetHours}
                    onChange={(e) => setTargetHours(e.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="hourly-rate">Hourly Rate ($)</Label>
                  <Input
                    id="hourly-rate"
                    type="number"
                    min="0"
                    step="0.01"
                    value={hourlyRate}
                    onChange={(e) => setHourlyRate(e.target.value)}
                  />
                </div>
              </div>

              <Button onClick={handleSaveSettings} disabled={isSaving}>
                <Save className="h-4 w-4 mr-2" />
                {isSaving ? 'Saving...' : 'Save Settings'}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="email" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Mail className="h-5 w-5" />
                Email Reports
              </CardTitle>
              <CardDescription>
                Configure automatic monthly progress reports with PDF attachment
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6" key={`email-settings-${emailEnabled}-${emailRecipient}-${emailSendDay}`}>
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="email-enabled">Enable Monthly Reports</Label>
                  <p className="text-sm text-muted-foreground">
                    Automatically send monthly progress reports with PDF
                  </p>
                </div>
                <Switch
                  id="email-enabled"
                  checked={emailEnabled}
                  onCheckedChange={handleEmailEnabledChange}
                />
              </div>

              <Separator />

              <div className={emailEnabled ? '' : 'opacity-50 pointer-events-none'}>
                <div className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="recipient">Recipient Email</Label>
                      <Input
                        id="recipient"
                        type="email"
                        placeholder="email@example.com"
                        value={emailRecipient}
                        onChange={(e) => setEmailRecipient(e.target.value)}
                        onBlur={handleEmailRecipientBlur}
                      />
                      <p className="text-xs text-muted-foreground">
                        Email address to receive monthly reports
                      </p>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="sendDay">Send on Day of Month</Label>
                      <Select 
                        value={String(emailSendDay)} 
                        onValueChange={handleEmailSendDayChange}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {Array.from({ length: 31 }, (_, i) => i + 1).map(day => (
                            <SelectItem key={day} value={String(day)}>
                              Day {day}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <p className="text-xs text-muted-foreground">
                        Report will be sent on this day each month
                      </p>
                    </div>
                  </div>

                  <div className="rounded-lg border p-4 bg-muted/50">
                    <h4 className="font-medium mb-2">What's included in the report:</h4>
                    <ul className="text-sm text-muted-foreground space-y-1">
                      <li>• Summary of previous month's hours</li>
                      <li>• Total entries logged</li>
                      <li>• Earnings calculation</li>
                      <li>• PDF attachment with detailed breakdown</li>
                    </ul>
                  </div>
                </div>
              </div>

              <div className="flex gap-2">
                {!emailSettingsLoaded && (
                  <Button onClick={() => handleSaveEmailSettings()} disabled={!emailEnabled || isSaving}>
                    <Save className="h-4 w-4 mr-2" />
                    {isSaving ? 'Saving...' : 'Save Email Settings'}
                  </Button>
                )}
                
                {emailSettingsLoaded && emailEnabled && (
                  <Button 
                    variant="outline" 
                    onClick={handleSendNow} 
                    disabled={isSendingNow}
                  >
                    <Send className="h-4 w-4 mr-2" />
                    {isSendingNow ? 'Sending...' : 'Send Report Now'}
                  </Button>
                )}
              </div>

              {!emailSettingsLoaded && (
                <p className="text-sm text-muted-foreground">
                  Configure and save your email settings to enable automatic reports
                </p>
              )}
              {emailSettingsLoaded && (
                <p className="text-sm text-muted-foreground">
                  Settings are saved automatically when you make changes
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <AddHoursDialog
        open={addHoursOpen}
        onOpenChange={setAddHoursOpen}
        onSubmit={handleAddHours}
      />
    </div>
  );
}
