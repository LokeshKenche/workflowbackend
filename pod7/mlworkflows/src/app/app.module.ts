import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { RouterModule, Routes } from '@angular/router';
import { HttpClientModule } from '@angular/common/http'; // Import for making HTTP requests

import { AppComponent } from './app.component';
import { SuggestionsComponent } from './suggestions/suggestions.component';

// Define your routes (adjust as needed)
const routes: Routes = [
  { path: '', component: AppComponent }, // Default route to AppComponent
  { path: 'suggestions', component: SuggestionsComponent } 
];

@NgModule({
  declarations: [
    AppComponent,
    SuggestionsComponent
  ],
  imports: [
    BrowserModule,
    HttpClientModule, // Add HttpClientModule for API calls
    RouterModule.forRoot(routes)
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }