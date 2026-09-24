document.addEventListener("DOMContentLoaded", function () {
    var elFc = document.getElementById("calendar-fc");
    var elOverview = document.getElementById("calendar-overview");
    var elTitle = document.getElementById("cal-title");
    var modeButtons = document.querySelectorAll(".cal-mode-btn");
    var prevBtn = document.getElementById("cal-prev");
    var nextBtn = document.getElementById("cal-next");
    var todayBtn = document.getElementById("cal-today");

    if (!elFc || !window.FullCalendar) return;

    var params = new URLSearchParams();
    if (elFc.dataset.categoryId) params.set("category_id", elFc.dataset.categoryId);
    if (elFc.dataset.personId) params.set("person_id", elFc.dataset.personId);
    if (elFc.dataset.status) params.set("status", elFc.dataset.status);
    var feedUrl = "/api/demarches/calendar?" + params.toString();

    var mode = "month";
    var refDate = new Date();
    var eventsByDate = {};
    var activePopover = null;

    function isoDate(d) {
        return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
    }

    function closePopover() {
        if (activePopover) {
            activePopover.remove();
            activePopover = null;
        }
    }
    document.addEventListener("click", function (e) {
        if (activePopover && !activePopover.contains(e.target) && !e.target.closest(".cal-mini-day")) {
            closePopover();
        }
    });
    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") closePopover();
    });

    var calendar = new FullCalendar.Calendar(elFc, {
        initialView: "dayGridMonth",
        locale: "fr",
        height: "auto",
        headerToolbar: false,
        events: feedUrl,
        eventDidMount: function () {
            if (window.lucide) lucide.createIcons();
        },
        datesSet: function (info) {
            if (mode === "month" || mode === "list") {
                elTitle.textContent = info.view.title;
                refDate = calendar.getDate();
            }
        },
    });
    calendar.render();

    function fetchEvents() {
        return fetch(feedUrl)
            .then(function (r) { return r.json(); })
            .then(function (events) {
                eventsByDate = {};
                events.forEach(function (ev) {
                    (eventsByDate[ev.start] = eventsByDate[ev.start] || []).push(ev);
                });
            });
    }

    function setActiveModeButton() {
        modeButtons.forEach(function (btn) {
            btn.classList.toggle("active", btn.dataset.mode === mode);
        });
    }

    function fitOverviewHeight() {
        if (elOverview.classList.contains("hidden")) return;
        var top = elOverview.getBoundingClientRect().top;
        var available = Math.max(360, window.innerHeight - top - 24);
        elOverview.style.height = available + "px";
    }

    function monthTitle(year, monthIndex) {
        return new Intl.DateTimeFormat("fr-FR", { month: "long", year: "numeric" }).format(new Date(year, monthIndex, 1));
    }

    function buildMiniMonth(year, monthIndex) {
        var wrap = document.createElement("div");
        wrap.className = "cal-mini-month";

        var title = document.createElement("div");
        title.className = "cal-mini-month-title";
        title.textContent = monthTitle(year, monthIndex);
        wrap.appendChild(title);

        var grid = document.createElement("div");
        grid.className = "cal-mini-grid";

        ["L", "M", "M", "J", "V", "S", "D"].forEach(function (w) {
            var wd = document.createElement("div");
            wd.className = "cal-mini-weekday";
            wd.textContent = w;
            grid.appendChild(wd);
        });

        var firstDow = (new Date(year, monthIndex, 1).getDay() + 6) % 7;
        var daysInMonth = new Date(year, monthIndex + 1, 0).getDate();
        var today = isoDate(new Date());
        var totalCells = Math.ceil((firstDow + daysInMonth) / 7) * 7;

        for (var i = 0; i < totalCells; i++) {
            var dayNum = i - firstDow + 1;
            var cell = document.createElement("div");
            cell.className = "cal-mini-day";

            if (dayNum < 1 || dayNum > daysInMonth) {
                cell.classList.add("is-outside");
            } else {
                var dateObj = new Date(year, monthIndex, dayNum);
                var iso = isoDate(dateObj);
                var label = document.createElement("span");
                label.textContent = dayNum;
                cell.appendChild(label);
                if (iso === today) cell.classList.add("is-today");

                var dayEvents = eventsByDate[iso];
                if (dayEvents && dayEvents.length) {
                    cell.classList.add("has-events");
                    var dots = document.createElement("div");
                    dots.className = "cal-mini-day-dots";
                    dayEvents.slice(0, 3).forEach(function (ev) {
                        var dot = document.createElement("span");
                        dot.className = "cal-mini-dot";
                        dot.style.background = ev.backgroundColor;
                        dots.appendChild(dot);
                    });
                    cell.appendChild(dots);
                    (function (cellRef, evs, d) {
                        cellRef.addEventListener("click", function (evClick) {
                            evClick.stopPropagation();
                            showPopover(cellRef, evs, d);
                        });
                    })(cell, dayEvents, dateObj);
                }
            }
            grid.appendChild(cell);
        }
        wrap.appendChild(grid);
        return wrap;
    }

    function showPopover(cell, events, dateObj) {
        closePopover();
        var pop = document.createElement("div");
        pop.className = "cal-popover";

        var title = document.createElement("div");
        title.className = "cal-popover-title";
        title.textContent = new Intl.DateTimeFormat("fr-FR", { day: "numeric", month: "long" }).format(dateObj);
        pop.appendChild(title);

        events.forEach(function (ev) {
            var a = document.createElement("a");
            a.href = ev.url;
            a.textContent = ev.title;
            pop.appendChild(a);
        });

        document.body.appendChild(pop);
        var rect = cell.getBoundingClientRect();
        var left = Math.min(rect.left, window.innerWidth - 220);
        pop.style.top = window.scrollY + rect.bottom + 4 + "px";
        pop.style.left = window.scrollX + Math.max(8, left) + "px";
        activePopover = pop;
    }

    function renderOverview() {
        elOverview.innerHTML = "";
        var count = mode === "six" ? 6 : 12;
        var cols = window.innerWidth < 768 ? 2 : mode === "six" ? 3 : 4;
        elOverview.style.gridTemplateColumns = "repeat(" + cols + ", 1fr)";
        elOverview.style.gridTemplateRows = "repeat(" + Math.ceil(count / cols) + ", 1fr)";

        var startYear = refDate.getFullYear();
        var startMonth = mode === "year" ? 0 : refDate.getMonth();

        for (var i = 0; i < count; i++) {
            var m = startMonth + i;
            var y = startYear + Math.floor(m / 12);
            var mi = ((m % 12) + 12) % 12;
            elOverview.appendChild(buildMiniMonth(y, mi));
        }
        if (window.lucide) lucide.createIcons();
        fitOverviewHeight();
    }

    function updateOverviewTitle() {
        if (mode === "year") {
            elTitle.textContent = String(refDate.getFullYear());
        } else if (mode === "six") {
            var start = new Date(refDate.getFullYear(), refDate.getMonth(), 1);
            var end = new Date(refDate.getFullYear(), refDate.getMonth() + 5, 1);
            var fmt = new Intl.DateTimeFormat("fr-FR", { month: "long", year: "numeric" });
            elTitle.textContent = fmt.format(start) + " – " + fmt.format(end);
        }
    }

    function refreshOverview() {
        updateOverviewTitle();
        renderOverview();
    }

    function applyMode(newMode) {
        mode = newMode;
        setActiveModeButton();
        closePopover();

        if (mode === "month" || mode === "list") {
            elOverview.classList.add("hidden");
            elFc.classList.remove("hidden");
            calendar.changeView(mode === "month" ? "dayGridMonth" : "listMonth");
            calendar.gotoDate(refDate);
        } else {
            elFc.classList.add("hidden");
            elOverview.classList.remove("hidden");
            refreshOverview();
        }
    }

    function navigate(dir, resetToday) {
        if (mode === "month" || mode === "list") {
            if (resetToday) calendar.today();
            else if (dir < 0) calendar.prev();
            else calendar.next();
            refDate = calendar.getDate();
            return;
        }
        if (resetToday) {
            refDate = new Date();
        } else {
            var months = mode === "six" ? 6 : 12;
            refDate = new Date(refDate.getFullYear(), refDate.getMonth() + dir * months, 1);
        }
        refreshOverview();
    }

    modeButtons.forEach(function (btn) {
        btn.addEventListener("click", function () { applyMode(btn.dataset.mode); });
    });
    prevBtn.addEventListener("click", function () { navigate(-1); });
    nextBtn.addEventListener("click", function () { navigate(1); });
    todayBtn.addEventListener("click", function () { navigate(0, true); });

    window.addEventListener("resize", function () {
        if (mode === "six" || mode === "year") renderOverview();
    });

    applyMode("month");
    fetchEvents().then(function () {
        if (mode === "six" || mode === "year") renderOverview();
    });
});
