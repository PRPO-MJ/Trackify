import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';

interface CreateGoalDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (goal: {
    name: string;
    description: string;
    targetHours: number;
    hourlyRate: number;
    endDate: string;
  }) => void;
}

export function CreateGoalDialog({ open, onOpenChange, onSubmit }: CreateGoalDialogProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [targetHours, setTargetHours] = useState('');
  const [hourlyRate, setHourlyRate] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  const handleSubmit = () => {
    if (!name.trim()) {
      toast.error('Please enter a goal name');
      return;
    }
    if (!targetHours || parseFloat(targetHours) <= 0) {
      toast.error('Please enter valid target hours');
      return;
    }

    onSubmit({
      name,
      description,
      targetHours: parseFloat(targetHours),
      hourlyRate: parseFloat(hourlyRate) || 0,
      endDate,
    });

    setName('');
    setDescription('');
    setTargetHours('');
    setHourlyRate('');
    setEndDate('');
    onOpenChange(false);
    toast.success('Goal created successfully');
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Create New Goal</DialogTitle>
          <DialogDescription>
            Set up a new goal to track your hours and progress.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="name">Goal Name</Label>
            <Input
              id="name"
              placeholder="e.g., Complete React Course"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              placeholder="Brief description of this goal..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="grid gap-2">
              <Label htmlFor="targetHours">Target Hours</Label>
              <Input
                id="targetHours"
                type="number"
                min="1"
                placeholder="100"
                value={targetHours}
                onChange={(e) => setTargetHours(e.target.value)}
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="hourlyRate">Hourly Rate ($)</Label>
              <Input
                id="hourlyRate"
                type="number"
                min="0"
                step="0.01"
                placeholder="0 for unpaid"
                value={hourlyRate}
                onChange={(e) => setHourlyRate(e.target.value)}
              />
            </div>
          </div>

          <div className="grid gap-2">
            <Label htmlFor="startDate">Target Start Date</Label>
            <Input
              id="startDate"
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="endDate">Target End Date</Label>
            <Input
              id="endDate"
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSubmit}>Create Goal</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
