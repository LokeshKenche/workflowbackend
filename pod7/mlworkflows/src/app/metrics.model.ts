// metrics.model.ts (create a new file)
// metric.model.ts 
export interface Metric {
    task_name: string;
    avg_duration: number; // Add this line
    cpu_usage: number;
    memory_usage: number;
    accuracy?: number; 
    suggestions?: string[]; 
  }