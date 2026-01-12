// VIEW: Pure presentational component for welcome header
interface WelcomeHeaderProps {
  firstName: string;
}

export function WelcomeHeader({ firstName }: WelcomeHeaderProps) {
  return (
    <div className="mb-8 animate-fade-in">
      <h1 className="text-3xl font-bold tracking-tight">
        Welcome back, {firstName}
      </h1>
      <p className="text-muted-foreground mt-1">
        Track your progress and achieve your goals
      </p>
    </div>
  );
}
