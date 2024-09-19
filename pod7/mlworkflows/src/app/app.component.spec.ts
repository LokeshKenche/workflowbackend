import { TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { AppComponent } from './app.component';
import { HttpClientTestingModule } from '@angular/common/http/testing'; // Import for mocking HTTP requests
import { MetricsService } from './metrics.service';
import { of } from 'rxjs'; // Import for creating observable

describe('AppComponent', () => {
  let metricsServiceSpy: jasmine.SpyObj<MetricsService>;

  beforeEach(async () => {
    // Create a spy object for MetricsService
    metricsServiceSpy = jasmine.createSpyObj('MetricsService', ['getPerformanceMetrics', 'startWorkflow']);

    await TestBed.configureTestingModule({
      imports: [
        RouterTestingModule,
        HttpClientTestingModule // Add for mocking HTTP requests
      ],
      declarations: [
        AppComponent
      ],
      providers: [
        { provide: MetricsService, useValue: metricsServiceSpy } // Provide the spy object
      ]
    }).compileComponents();
  });

  it('should create the app', () => {
    const fixture = TestBed.createComponent(AppComponent);
    const app = fixture.componentInstance;
    expect(app).toBeTruthy();
  });

  it('should fetch metrics on init', () => {
    // Mock the getPerformanceMetrics response
    const mockMetricsData = {
      all_runs_avg_metrics: [],
      latest_run_metrics: {}
    };
    metricsServiceSpy.getPerformanceMetrics.and.returnValue(of(mockMetricsData));

    const fixture = TestBed.createComponent(AppComponent);
    fixture.detectChanges(); // Trigger ngOnInit

    expect(metricsServiceSpy.getPerformanceMetrics).toHaveBeenCalled();
    expect(fixture.componentInstance.averageMetrics).toEqual(mockMetricsData.all_runs_avg_metrics);
    expect(fixture.componentInstance.latestRunMetrics).toEqual(mockMetricsData.latest_run_metrics);
  });

  // ... (You can add more test cases as needed to cover other functionalities)
});