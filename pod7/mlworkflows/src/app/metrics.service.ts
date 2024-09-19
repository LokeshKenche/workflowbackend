import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class MetricsService {
  private apiUrl = 'http://localhost:5000'; // Replace with your Flask API URL

  constructor(private http: HttpClient) { }

  startWorkflow(): Observable<any> {
    return this.http.post(`${this.apiUrl}/start_workflow`, {});
  }

  getPerformanceMetrics(): Observable<any> {
    return this.http.get(`${this.apiUrl}/get_performance_metrics`);
  }
}