import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";
import frLocale from "@fullcalendar/core/locales/fr";

export default function AdminCalendar() {
  return (
    <FullCalendar
      events="/api/lab/calendar"
      plugins={[dayGridPlugin]}
      initialView="dayGridMonth"
      headerToolbar={{
        left: "",
        center: "title",
        right: "prev,next",
      }}
      locale={frLocale}
      eventClassNames={() => `fr-background-contrast--blue-france`}
    />
  );
}
