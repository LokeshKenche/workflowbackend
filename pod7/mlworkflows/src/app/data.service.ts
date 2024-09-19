import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class DataService {

  private apiUrl = 'http://127.0.0.1:5000'; // Replace with your actual API endpoint

  constructor(private http: HttpClient) { }

  // Method to get metrics data
  getMetrics(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/get_performance_metrics`);
  }

  // Method to get average performance data
  getAveragePerformance(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/average-performance`);
  }

  // Method to get suggestions from the ML model
  getSuggestions(): Observable<string[]> {
    return this.http.get<string[]>(`${this.apiUrl}/suggestions`);
  }
}
