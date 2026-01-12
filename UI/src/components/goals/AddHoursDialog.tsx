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
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { CalendarIcon } from 'lucide-react';
import { format, differenceInMinutes } from 'date-fns';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';

interface AddHoursDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (entry: {
    date: string;
    startTime: string;
    endTime: string;
    minutes: number;
    description: string;
  }) => void;
}
export function AddHoursDialog({ open, onOpenChange, onSubmit }: AddHoursDialogProps) {
  const [date, setDate] = useState<Date>(new Date());
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');
  const [description, setDescription] = useState('');

  const handleSubmit = () => {
    if (!startTime || !endTime) {
      toast.error('Please enter start and end times');
      return;
    }

    const start = new Date(`${format(date, 'yyyy-MM-dd')}T${startTime}`);
    const end = new Date(`${format(date, 'yyyy-MM-dd')}T${endTime}`);

    if (end <= start) {
      toast.error('End time must be after start time');
      return;
    }

    const minutes = differenceInMinutes(end, start);
    const hours = Math.floor(differenceInMinutes(end, start) / 60);
    const remaining = minutes % 60;

    onSubmit({
      date: format(date, 'yyyy-MM-dd'),
      startTime,
      endTime,
      minutes,
      description,
    });

    setStartTime('');
    setEndTime('');
    setDescription('');
    setDate(new Date());
    onOpenChange(false);

    toast.success(`Logged ${hours} hours and ${remaining} minutes.`);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Log Work Hours</DialogTitle>
          <DialogDescription>
            Select a date and the time range you worked.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          {/* Date */}
          <div className="grid gap-2">
            <Label>Date</Label>
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  className={cn(
                    'w-full justify-start text-left font-normal',
                    !date && 'text-muted-foreground'
                  )}
                >
                  <CalendarIcon className="mr-2 h-4 w-4" />
                  {format(date, 'PPP')}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0">
                <Calendar
                  mode="single"
                  selected={date}
                  onSelect={(d) => d && setDate(d)}
                  initialFocus
                />
              </PopoverContent>
            </Popover>
          </div>

          {/* Time range */}
          <div className="grid grid-cols-2 gap-4">
            <div className="grid gap-2">
              <Label htmlFor="start">Start Time</Label>
              <Input
                id="start"
                type="time"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="end">End Time</Label>
              <Input
                id="end"
                type="time"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
              />
            </div>
          </div>

          {/* Description */}
          <div className="grid gap-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              placeholder="What did you work on?"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSubmit}>Log Hours</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}