// MODEL: User data layer
import { User } from '@/types/goal';

export class UserModel {
  private user: User | null;

  constructor(initialUser: User | null = null) {
    this.user = initialUser ? { ...initialUser } : null;
  }

  // Get current user
  getUser(): User {
    return { ...this.user };
  }

  // Update user
  update(data: Partial<User>): User {
    this.user = { ...this.user, ...data };
    return this.user;
  }

  // Get user's first name
  getFirstName(): string {
    return this.user.name.split(' ')[0];
  }
}

// Singleton instance
export const userModel = new UserModel();
