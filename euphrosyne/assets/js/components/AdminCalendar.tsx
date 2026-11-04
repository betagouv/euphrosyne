import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/react/daygrid";
import classicThemePlugin from "@fullcalendar/react/themes/classic";
import frLocale from "@fullcalendar/react/locales/fr";

export default function AdminCalendar() {
  return (
    <FullCalendar
      events="/api/lab/calendar"
      plugins={[dayGridPlugin, classicThemePlugin]}
      initialView="dayGridMonth"
      headerToolbar={{
        start: "",
        center: "title",
        end: "prev,next",
      }}
      locale={frLocale}
      eventDisplay="block"
    />
  );
}
