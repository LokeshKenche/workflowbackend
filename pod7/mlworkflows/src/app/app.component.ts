import { Component, OnInit } from '@angular/core';
import { MetricsService } from './metrics.service';
import { Router } from '@angular/router';
import { Metric } from './metrics.model';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit {
  averageMetrics: Metric[] = [];
  latestRunMetrics: { [key: string]: Metric } = {};

  constructor(private metricsService: MetricsService, private router: Router) { }

  ngOnInit() {
    this.fetchMetrics(); 
  }

  startWorkflow() {
    this.metricsService.startWorkflow().subscribe(
      (response) => {
        console.log('Workflow started successfully:', response);
        setTimeout(() => this.fetchMetrics(), 5000); 
      },
      (error) => {
        console.error('Error starting workflow:', error);
        // Handle the error gracefully in your UI
      }
    );
  }

  fetchMetrics() {
    this.metricsService.getPerformanceMetrics().subscribe(
      (data) => {
        this.averageMetrics = data.all_runs_avg_metrics as Metric[]; // Type assertion here
        this.latestRunMetrics = data.latest_run_metrics as { [key: string]: Metric };
      },
      (error) => {
        console.error('Error fetching metrics:', error);
        // Handle the error gracefully in your UI
      }
    );
  }

  viewSuggestions() {
    this.router.navigate(['/suggestions'], { state: { latestRunMetrics: this.latestRunMetrics } });
  }
}