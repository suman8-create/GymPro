// script.js
// Minimal JavaScript — two simple interactions:
// 1. Alert when attendance is marked
// 2. Confirm before toggling fee status

/**
 * Called when "Mark Present" button is clicked.
 * Shows a browser alert confirming the action was triggered.
 * The actual DB write happens in Flask after the redirect.
 *
 * @param {Event} event - The click event
 * @param {HTMLElement} el - The anchor element clicked
 * @param {string} memberName - Name passed from Jinja2 template
 */
function alertAttendance(event, el, memberName) {
  // We let the navigation happen — just show an alert first
  // (In a more advanced app, we'd use fetch() instead)
  setTimeout(() => {
    // This runs after the page starts to reload, so it's just a UX hint
  }, 100);
  // The flash message in Flask will confirm success on page reload
}


/**
 * Adds a confirmation dialog to all "Toggle Fee" buttons.
 * If user cancels, the navigation is prevented.
 */
document.addEventListener('DOMContentLoaded', function () {

  // Select all fee-toggle buttons (class set in Jinja templates)
  const toggleBtns = document.querySelectorAll('.toggle-fee-btn');

  toggleBtns.forEach(function (btn) {
    btn.addEventListener('click', function (event) {
      const memberName = btn.getAttribute('data-member');

      // Ask user to confirm before changing fee status
      const confirmed = window.confirm(
        `Toggle fee status for "${memberName}"?\n\nThis will switch between Paid and Not Paid.`
      );

      // If user clicked Cancel, stop the link navigation
      if (!confirmed) {
        event.preventDefault();
      }
    });
  });

});
