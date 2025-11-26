# Frontend Testing Checklist

**Purpose**: Comprehensive manual testing checklist for all frontend pages and features  
**Date**: November 18, 2025  
**Testing Type**: Manual / Human Testing

---

## 📋 Pre-Testing Setup

### Environment Setup
- [ ] Backend API is running at `http://localhost:8000`
- [ ] Frontend development server is running
- [ ] Browser console is open (F12) to check for errors
- [ ] Network tab is open to monitor API calls
- [ ] Test data exists (snapshots, trades, etc.)

### Browser Testing
- [ ] Test in Chrome/Edge
- [ ] Test in Firefox
- [ ] Test in Safari (if on Mac)
- [ ] Test responsive design (mobile, tablet, desktop)

---

## 🏠 Navigation & General

### Navigation
- [ ] All navigation links work correctly
- [ ] Active page is highlighted in navigation
- [ ] Page titles are correct
- [ ] Browser back/forward buttons work
- [ ] Page refresh maintains state where appropriate

### Error Handling
- [ ] 404 page displays for invalid routes
- [ ] Network errors show user-friendly messages
- [ ] API errors are handled gracefully
- [ ] Loading states display correctly
- [ ] Empty states display when no data

### Performance
- [ ] Pages load within reasonable time (< 3 seconds)
- [ ] No console errors on page load
- [ ] No console warnings (or acceptable warnings)
- [ ] Images/icons load correctly
- [ ] No memory leaks (check after extended use)

---

## 📊 Live Trading Dashboard

### Page Load
- [ ] Page loads without errors
- [ ] Loading indicator shows while fetching data
- [ ] All sections render correctly
- [ ] No console errors

### Station Filter
- [ ] Station dropdown populates with available stations
- [ ] Station names display correctly
- [ ] **Venue icons display next to station names** ⭐
- [ ] Selecting a station filters data correctly
- [ ] "All Stations" option works
- [ ] Filter persists on page refresh (if implemented)

### Event Day Selector
- [ ] Event day dropdown populates with available days
- [ ] Today + future days are shown
- [ ] Selecting an event day filters data correctly
- [ ] "All Days" option works (if available)

### Active Filter Label
- [ ] Selected station displays with icon ⭐
- [ ] Selected event day displays
- [ ] Clear/reset filter button works (if available)

### Zeus Forecast Evolution Graph
- [ ] Graph displays correctly
- [ ] X-axis shows correct time range (00:00-24:00)
- [ ] Y-axis shows temperature correctly
- [ ] Data points plot at correct times
- [ ] Zeus Median line displays (if implemented)
- [ ] METAR overlay displays (if available)
- [ ] Tooltips show correct values on hover
- [ ] Graph updates when filters change
- [ ] Graph handles empty data gracefully

### METAR Data Display
- [ ] METAR observations display for today
- [ ] "Not yet" displays for future days
- [ ] Temperature values are correct
- [ ] Observation times are correct
- [ ] Data updates when filters change

### Polymarket Probabilities
- [ ] Market probabilities display correctly
- [ ] Bracket names are correct
- [ ] Probability values are formatted correctly (0-100% or 0-1)
- [ ] Data updates when filters change

### Trading Decisions / Edges
- [ ] Edges table displays correctly
- [ ] All columns show correct data:
  - [ ] Bracket name
  - [ ] Edge percentage
  - [ ] Size (USD)
  - [ ] Zeus probability
  - [ ] Market probability
- [ ] Sorting works (if implemented)
- [ ] Data updates when filters change
- [ ] Empty state shows when no edges

### Live Agent Activity Log
- [ ] Log entries display correctly
- [ ] Timestamps are formatted correctly
- [ ] Log levels are color-coded (if implemented)
- [ ] Station filter works
- [ ] Event day filter works
- [ ] Action type filter works
- [ ] Log level filter works
- [ ] Pagination works (if implemented)
- [ ] Auto-scroll works (if implemented)
- [ ] Log entries are in correct order (newest first/last)

### Status Display
- [ ] Engine status displays (RUNNING/STOPPED)
- [ ] Execution mode displays (PAPER/LIVE)
- [ ] Timer shows correct countdown ⭐
- [ ] Timer updates every second
- [ ] Next cycle time displays correctly
- [ ] Last cycle time displays correctly

### WebSocket Updates
- [ ] Real-time updates work (if engine is running)
- [ ] New snapshots trigger updates
- [ ] New trades trigger updates
- [ ] Edge updates trigger updates
- [ ] Connection status displays (if implemented)
- [ ] Reconnection works after disconnect

---

## 📈 Historical Data Page

### Page Load
- [ ] Page loads without errors
- [ ] Loading indicator shows while fetching data
- [ ] All sections render correctly

### Station Filter
- [ ] Station dropdown populates
- [ ] **Venue icons display next to station names** ⭐
- [ ] Filtering works correctly

### Event Day Filter
- [ ] Event day dropdown populates
- [ ] Historical dates are available
- [ ] Filtering works correctly

### Zeus/METAR Comparison Graph
- [ ] Graph displays correctly
- [ ] X-axis spans full 24 hours (00:00-24:00)
- [ ] X-axis labels are readable (hourly or subset)
- [ ] All data points are plotted (even if sparse)
- [ ] Zeus forecast line displays
- [ ] METAR observations display
- [ ] Tooltips show correct values
- [ ] Graph handles missing data gracefully

### Polymarket Probabilities Graph
- [ ] Graph displays correctly
- [ ] X-axis aligns with Zeus/METAR graph
- [ ] All brackets display
- [ ] Probability lines are distinguishable
- [ ] Tooltips work correctly

### Trading Decisions Graph
- [ ] Graph displays correctly
- [ ] X-axis aligns with other graphs
- [ ] Trade markers display at correct times
- [ ] Trade details show on hover
- [ ] Win/loss indicators work (if implemented)

### Graph Synchronization
- [ ] All three graphs share same X-axis scale
- [ ] Zooming (if implemented) affects all graphs
- [ ] Panning (if implemented) affects all graphs
- [ ] Time alignment is correct across graphs

### Data Accuracy
- [ ] Data matches backend API responses
- [ ] Timestamps are correct
- [ ] Values are correct
- [ ] No data corruption

---

## ⚙️ Configuration Page

### Page Load
- [ ] Page loads without errors
- [ ] All sections render correctly
- [ ] Current config values display correctly

### Engine Control Section
- [ ] Start button works
- [ ] Stop button works
- [ ] Restart button works
- [ ] Status updates after actions
- [ ] Error messages display if actions fail
- [ ] Loading states display during actions

### Active Stations Selector
- [ ] All stations are listed
- [ ] **Venue icons display next to station names** ⭐
- [ ] Checkboxes work correctly
- [ ] Selected stations persist
- [ ] Save button works
- [ ] Validation works (at least one station required)

### Trading Parameters Section (Collapsible)
- [ ] Section expands/collapses correctly
- [ ] All fields display:
  - [ ] Edge Min
  - [ ] Fee BP
  - [ ] Slippage BP
  - [ ] Kelly Cap
  - [ ] Per Market Cap
  - [ ] Liquidity Min USD
  - [ ] Daily Bankroll Cap
- [ ] Tooltips display on hover (if implemented)
- [ ] Input validation works
- [ ] Save button works
- [ ] Values persist after save

### Probability Model Section (Collapsible)
- [ ] Section expands/collapses correctly
- [ ] Model Mode dropdown works (spread/bands)
- [ ] Zeus Likely PCT field works
- [ ] Zeus Possible PCT field works
- [ ] Tooltips display on hover (if implemented)
- [ ] Input validation works
- [ ] Save button works

### Dynamic Trading Section (Collapsible)
- [ ] Section expands/collapses correctly
- [ ] Interval Seconds field works
- [ ] Lookahead Days field works
- [ ] Input validation works
- [ ] Save button works

### API Keys Section (Collapsible)
- [ ] Section expands/collapses correctly
- [ ] Keys are masked (showing ****)
- [ ] Update functionality works (if implemented)
- [ ] Security warnings display (if implemented)

### Configuration Actions
- [ ] Save button saves all changes
- [ ] Reset to defaults button works
- [ ] Validation errors display correctly
- [ ] Success messages display
- [ ] Error messages display
- [ ] Changes require restart warning (if applicable)

---

## 🧪 Backtest Configuration & Results

### Backtest Configuration
- [ ] Page loads without errors
- [ ] All fields display:
  - [ ] Start Date picker
  - [ ] End Date picker
  - [ ] Station radio buttons
  - [ ] **Venue icons display next to station names** ⭐
  - [ ] Model Mode dropdown
  - [ ] Zeus Likely PCT
  - [ ] Zeus Possible PCT
  - [ ] Edge Min
  - [ ] Fee BP
  - [ ] Slippage BP
  - [ ] Kelly Cap
  - [ ] Per Market Cap
  - [ ] Liquidity Min USD
- [ ] Tooltips display on hover
- [ ] Input validation works
- [ ] Date validation works (end > start)
- [ ] Run Backtest button works

### Backtest Execution
- [ ] Loading state displays during backtest
- [ ] Progress indicator works (if implemented)
- [ ] Cancel button works (if implemented)
- [ ] Error handling works

### Backtest Results
- [ ] Results page displays after completion
- [ ] Summary statistics display:
  - [ ] Total trades
  - [ ] Wins/Losses/Pending
  - [ ] Win rate
  - [ ] Total P&L
  - [ ] ROI
- [ ] Trade list displays correctly
- [ ] Filters work (if implemented)
- [ ] Export to CSV works (if implemented)
- [ ] Results are accurate

---

## 💰 Performance & Portfolio Page

### Page Load
- [ ] Page loads without errors
- [ ] All sections render correctly

### Mode Toggle
- [ ] Paper/Live toggle works
- [ ] Mode persists during session
- [ ] Appropriate warnings/info display

### Account Balances Section
- [ ] Paper mode displays simulated balances
- [ ] Starting balance displays correctly
- [ ] Current balance calculates correctly
- [ ] P&L displays correctly
- [ ] Live mode shows placeholder (if not implemented)
- [ ] Formatting is correct (currency, decimals)

### P&L Dashboard Section
- [ ] Period selector works (Today/Week/Month/Year/All Time)
- [ ] P&L values display correctly
- [ ] ROI displays correctly
- [ ] Total Risk displays correctly
- [ ] Breakdown by Venue displays
- [ ] Breakdown by Station displays
- [ ] **Venue icons display in breakdowns** ⭐
- [ ] Values update when period changes
- [ ] Formatting is correct

### Performance Metrics Section
- [ ] All metrics display:
  - [ ] Total Trades
  - [ ] Resolved/Pending counts
  - [ ] Win Rate
  - [ ] Average Edge
  - [ ] ROI
  - [ ] Sharpe Ratio
  - [ ] Largest Win/Loss
- [ ] Station breakdown displays
- [ ] Values are accurate
- [ ] Formatting is correct

### Trade History Table
- [ ] Table displays correctly
- [ ] All columns show:
  - [ ] Date
  - [ ] Station
  - [ ] Bracket
  - [ ] Size
  - [ ] Edge
  - [ ] Outcome (Win/Loss/Pending)
  - [ ] P&L
  - [ ] Venue
- [ ] Filters work:
  - [ ] Date range
  - [ ] Station
  - [ ] Venue
  - [ ] Outcome
- [ ] Pagination works
- [ ] Sorting works (if implemented)
- [ ] Outcome icons display correctly (✅/❌/⏳)
- [ ] P&L color coding works (green/red)

### Trade Resolution
- [ ] Resolve Trades button works
- [ ] Resolution process shows progress
- [ ] Resolved trades update correctly
- [ ] P&L updates after resolution
- [ ] Error handling works

---

## 🔍 Activity Logs Page (if separate page)

### Page Load
- [ ] Page loads without errors
- [ ] Log entries display

### Filters
- [ ] Station filter works
- [ ] Event day filter works
- [ ] Action type filter works
- [ ] Log level filter works
- [ ] Date range filter works (if implemented)

### Display
- [ ] Log entries format correctly
- [ ] Timestamps are readable
- [ ] Log levels are color-coded
- [ ] Pagination works
- [ ] Auto-refresh works (if implemented)

---

## 🎨 UI/UX Elements

### Icons & Images
- [ ] **Venue icons display correctly everywhere** ⭐
- [ ] Icons are properly sized
- [ ] Icons align correctly with text
- [ ] Icons are not pixelated
- [ ] Icons have appropriate alt text

### Colors & Styling
- [ ] Color scheme is consistent
- [ ] Positive values are green
- [ ] Negative values are red
- [ ] Warning messages are yellow/orange
- [ ] Error messages are red
- [ ] Success messages are green

### Typography
- [ ] Fonts load correctly
- [ ] Text is readable
- [ ] Font sizes are appropriate
- [ ] Headings are properly sized

### Spacing & Layout
- [ ] Elements are properly spaced
- [ ] No overlapping elements
- [ ] Layout is responsive
- [ ] Mobile view works correctly
- [ ] Tablet view works correctly
- [ ] Desktop view works correctly

### Interactive Elements
- [ ] Buttons are clickable
- [ ] Hover states work
- [ ] Focus states work (keyboard navigation)
- [ ] Disabled states are clear
- [ ] Loading states are clear

### Forms
- [ ] Input fields are accessible
- [ ] Labels are associated with inputs
- [ ] Validation messages are clear
- [ ] Required fields are marked
- [ ] Form submission works

---

## 🔌 API Integration

### API Calls
- [ ] All API calls use correct endpoints
- [ ] Request parameters are correct
- [ ] Response handling works
- [ ] Error responses are handled
- [ ] Loading states show during API calls

### Data Formatting
- [ ] Dates format correctly
- [ ] Numbers format correctly (decimals, currency)
- [ ] Percentages format correctly
- [ ] Timezones are handled correctly

### Caching
- [ ] Station data is cached (if implemented)
- [ ] Cache invalidation works (if implemented)
- [ ] Stale data doesn't persist

---

## 🐛 Error Scenarios

### Network Errors
- [ ] API server down shows error message
- [ ] Network timeout shows error message
- [ ] 404 errors are handled
- [ ] 500 errors are handled
- [ ] Retry mechanism works (if implemented)

### Data Errors
- [ ] Missing data shows empty state
- [ ] Invalid data is handled gracefully
- [ ] Malformed responses are handled
- [ ] Null/undefined values don't break UI

### User Errors
- [ ] Invalid input shows validation error
- [ ] Required fields are enforced
- [ ] Out of range values are rejected
- [ ] Confirmation dialogs work (if implemented)

---

## ♿ Accessibility

### Keyboard Navigation
- [ ] Tab order is logical
- [ ] All interactive elements are keyboard accessible
- [ ] Focus indicators are visible
- [ ] Escape key closes modals/dropdowns

### Screen Readers
- [ ] Alt text on images
- [ ] ARIA labels on buttons
- [ ] Form labels are associated
- [ ] Error messages are announced

### Visual
- [ ] Color contrast is sufficient
- [ ] Text is readable at different sizes
- [ ] Icons have text alternatives

---

## 📱 Responsive Design

### Mobile (< 768px)
- [ ] Navigation works (hamburger menu if implemented)
- [ ] Tables scroll horizontally or stack
- [ ] Forms are usable
- [ ] Buttons are appropriately sized
- [ ] Text is readable
- [ ] Graphs/charts are readable

### Tablet (768px - 1024px)
- [ ] Layout adapts correctly
- [ ] All features are accessible
- [ ] Touch targets are appropriate

### Desktop (> 1024px)
- [ ] Full layout displays
- [ ] All features are accessible
- [ ] Hover states work

---

## 🔄 State Management

### Page State
- [ ] Filters persist during navigation (if implemented)
- [ ] Selected items persist (if implemented)
- [ ] Form data persists (if implemented)
- [ ] State resets appropriately

### Data State
- [ ] Data refreshes when needed
- [ ] Stale data doesn't display
- [ ] Loading states are accurate
- [ ] Error states are accurate

---

## ⚡ Performance

### Load Times
- [ ] Initial page load < 3 seconds
- [ ] Subsequent navigation < 1 second
- [ ] API calls complete in reasonable time
- [ ] Images load efficiently

### Resource Usage
- [ ] No memory leaks
- [ ] CPU usage is reasonable
- [ ] Network usage is reasonable
- [ ] No unnecessary re-renders

---

## 🧪 Edge Cases

### Empty States
- [ ] No stations available
- [ ] No trades available
- [ ] No snapshots available
- [ ] No edges available
- [ ] Empty filters show appropriate message

### Large Data Sets
- [ ] Many stations handle correctly
- [ ] Many trades paginate correctly
- [ ] Many log entries paginate correctly
- [ ] Graphs handle many data points

### Special Characters
- [ ] Station codes with special chars (if any)
- [ ] City names with special chars
- [ ] Bracket names with special chars (°F, ≤, ≥)

### Time Zones
- [ ] Times display in correct timezone
- [ ] Date boundaries are correct
- [ ] DST transitions are handled

---

## ✅ Final Checks

### Cross-Browser
- [ ] Chrome/Edge works
- [ ] Firefox works
- [ ] Safari works (if applicable)

### Documentation
- [ ] All features match documentation
- [ ] Error messages are helpful
- [ ] Tooltips are accurate

### User Experience
- [ ] Flow is intuitive
- [ ] Actions are clear
- [ ] Feedback is immediate
- [ ] Errors are recoverable

---

## 📝 Notes Section

**Use this space to document any issues found:**

```
Issue 1: [Description]
Location: [Page/Component]
Severity: [Critical/High/Medium/Low]
Status: [Open/Fixed/Deferred]

Issue 2: [Description]
...
```

---

## 🎯 Priority Testing

**If time is limited, focus on these critical areas:**

1. ⭐ **Venue Icons** - Display correctly in all 5 locations
2. ⭐ **Timer** - Updates correctly, shows next cycle time
3. ⭐ **Live Dashboard** - All filters and graphs work
4. ⭐ **Configuration Page** - Engine control and station selection
5. ⭐ **Performance Page** - P&L calculations and trade resolution

---

**Testing Date**: _______________  
**Tester**: _______________  
**Browser**: _______________  
**Backend Version**: _______________  
**Frontend Version**: _______________


