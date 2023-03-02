import { Calendar } from "@fullcalendar/core";
import dayGridPlugin from "@fullcalendar/daygrid";
import frLocale from "@fullcalendar/core/locales/fr";
import listPlugin from "@fullcalendar/list";

export class AdminCalendar extends HTMLDivElement {
  render() {
    const calendar = new Calendar(this, {
      events: "/api/lab/calendar",
      plugins: [dayGridPlugin, listPlugin],
      initialView: "dayGridMonth",
      views: {
        timeGridFourDay: {
          type: "list",
          visibleRange: function (currentDate) {
            // Generate a new date for manipulating in the next step
            var startDate = new Date(currentDate.valueOf());
            var endDate = new Date(currentDate.valueOf());

            // Adjust the start & end dates, respectively
            startDate.setDate(startDate.getDate() - 1); // One day in the past
            endDate.setDate(endDate.getDate() + 60); // 30 days into the future

            return { start: startDate, end: endDate };
          },
          buttonText: window.gettext("Upcoming"),
        },
      },
      headerToolbar: {
        left: "prev,next",
        center: "title",
        right: "dayGridMonth,timeGridFourDay", // user can switch between the two
      },
      locale: frLocale,
      eventClassNames: () => `fr-background-contrast--blue-france`,
    });
    calendar.render();
  }

  static init() {
    customElements.define("admin-calendar", AdminCalendar, { extends: "div" });
  }
}
