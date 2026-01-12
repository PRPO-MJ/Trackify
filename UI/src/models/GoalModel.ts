// MODEL: Data layer - handles data operations and business logic
import { Goal, WorkEntry } from '@/types/goal';

export class GoalModel {
  private goals: Goal[];

  constructor(initialGoals: Goal[] = []) {
    this.goals = [...initialGoals];
  }

  // Get all goals
  getAll(): Goal[] {
    return [...this.goals];
  }

  // Get goal by ID
  getById(id: string): Goal | undefined {
    return this.goals.find(g => g.id === id);
  }

  // Get active goals (not completed)
  getActive(): Goal[] {
    return this.goals.filter(g => g.completedHours < g.targetHours);
  }

  // Get completed goals
  getCompleted(): Goal[] {
    return this.goals.filter(g => g.completedHours >= g.targetHours);
  }

  // Create a new goal
  create(data: {
    name: string;
    description: string;
    targetHours: number;
    hourlyRate: number;
    endDate: string;
  }): Goal {
    const newGoal: Goal = {
      id: String(Date.now()),
      name: data.name,
      description: data.description,
      targetHours: data.targetHours,
      completedHours: 0,
      hourlyRate: data.hourlyRate,
      currency: 'USD',
      startDate: new Date().toISOString().split('T')[0],
      endDate: data.endDate || new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      workEntries: [],
      emailSettings: {
        enabled: false,
        recipients: [],
        subject: '',
        body: '',
        frequency: 'weekly',
      },
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    this.goals = [newGoal, ...this.goals];
    return newGoal;
  }

  // Update a goal
  update(id: string, data: Partial<Goal>): Goal | undefined {
    const index = this.goals.findIndex(g => g.id === id);
    if (index === -1) return undefined;
    
    this.goals[index] = {
      ...this.goals[index],
      ...data,
      updatedAt: new Date().toISOString(),
    };
    return this.goals[index];
  }

  // Delete a goal
  delete(id: string): boolean {
    const index = this.goals.findIndex(g => g.id === id);
    if (index === -1) return false;
    this.goals.splice(index, 1);
    return true;
  }

  // Add work entry to a goal
  addWorkEntry(goalId: string, entry: Omit<WorkEntry, 'id'>): Goal | undefined {
    const goal = this.getById(goalId);
    if (!goal) return undefined;

    const newEntry: WorkEntry = {
      ...entry,
      id: String(Date.now()),
    };

    return this.update(goalId, {
      workEntries: [...goal.workEntries, newEntry],
      completedHours: goal.completedHours + entry.hours,
    });
  }

  // Calculate statistics
  getStatistics(): {
    totalHours: number;
    totalTarget: number;
    totalEarned: number;
    activeCount: number;
    completedCount: number;
  } {
    return {
      totalHours: this.goals.reduce((sum, g) => sum + g.completedHours, 0),
      totalTarget: this.goals.reduce((sum, g) => sum + g.targetHours, 0),
      totalEarned: this.goals.reduce((sum, g) => sum + g.completedHours * g.hourlyRate, 0),
      activeCount: this.getActive().length,
      completedCount: this.getCompleted().length,
    };
  }
}

// Singleton instance for the application
export const goalModel = new GoalModel();
