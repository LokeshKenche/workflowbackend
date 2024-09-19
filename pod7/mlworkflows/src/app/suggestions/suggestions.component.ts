import { Component, OnInit, Input } from '@angular/core';
import { Metric } from '../metrics.model'; // Import the Metric interface

@Component({
  selector: 'app-suggestions',
  templateUrl: './suggestions.component.html',
  styleUrls: ['./suggestions.component.css']
})
export class SuggestionsComponent implements OnInit {
  @Input() latestRunMetrics: { [key: string]: Metric } = {}; // Use the Metric interface

  constructor() { } // You don't need the Router here anymore

  ngOnInit() {
    // You don't need to retrieve from router state anymore, as it's passed as an Input
  }
}