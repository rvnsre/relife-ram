"""On-demand, offline ReLife Education Center for the live desktop."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tkinter as tk
from tkinter import filedialog, font, messagebox, ttk

import appearance
import learning


class Education:
    def __init__(self, root):
        self.root = root
        self.cards = []
        self.current = None
        self.focus_timer = None
        root.title("ReLife · Təhsil mərkəzi")
        root.geometry(f"{min(840, root.winfo_screenwidth() - 20)}x{min(660, root.winfo_screenheight() - 65)}")
        root.minsize(610, 480)
        appearance.configure(root)
        ttk.Label(root, text="Təhsil mərkəzi", style="Header.TLabel").pack(fill="x")
        tabs = ttk.Notebook(root)
        tabs.pack(fill="both", expand=True, padx=12, pady=12)
        tabs.enable_traversal()
        root.bind("<Control-plus>", lambda event: self.set_text_size(1))
        root.bind("<Control-minus>", lambda event: self.set_text_size(-1))
        self.tabs = tabs
        for label, populate in (
            ("Kitabxana", self.library), ("Təkrar", self.flashcards), ("Müəllim", self.teacher),
            ("Elm", self.science), ("Plan", self.planner), ("Qeydlər", self.notes), ("Fokus", self.focus),
            ("Kömək", self.help), ("Onlayn AI", self.ai),
        ):
            pane = ttk.Frame(tabs, padding=12)
            tabs.add(pane, text=label)
            populate(pane)
        ttk.Label(root, text="RAM sessiyası bitməzdən əvvəl işinizi xarici yaddaşa ixrac edin.", style="Caption.TLabel").pack(
            anchor="w", padx=14, pady=(0, 9)
        )

    def set_text_size(self, delta):
        for name in ("TkDefaultFont", "TkTextFont", "TkHeadingFont"):
            current = font.nametofont(name)
            current.configure(size=min(18, max(10, current.cget("size") + delta)))

    def entry(self, parent, label, value=""):
        label_style = "Practice.TLabel" if parent.cget("style") == "Practice.TFrame" else "TLabel"
        ttk.Label(parent, text=label, style=label_style).pack(anchor="w")
        entry = ttk.Entry(parent)
        entry.insert(0, value)
        entry.pack(fill="x", pady=(2, 7))
        return entry

    def actions(self, parent, *actions):
        row = ttk.Frame(parent)
        row.pack(anchor="w", pady=(2, 6))
        for index, (title, command) in enumerate(actions):
            style = "Primary.TButton" if index == 0 else "TButton"
            ttk.Button(row, text=title, command=command, style=style).pack(side="left", padx=(0, 6))
        return row

    def output(self, parent, height=4, editable=False):
        box = tk.Text(parent, wrap="word", height=height, width=1, padx=12, pady=10, font="TkTextFont",
                      background="#ffffff", foreground=appearance.INK, insertbackground=appearance.INK,
                      relief="flat", borderwidth=0, highlightthickness=1,
                      highlightbackground=appearance.BORDER, highlightcolor=appearance.ACCENT,
                      selectbackground=appearance.ACCENT, selectforeground="#ffffff")
        box.pack(fill="both", expand=True, pady=(2, 7))
        if not editable:
            box.configure(state="disabled")
        return box

    @staticmethod
    def show(box, text):
        box.configure(state="normal")
        box.delete("1.0", "end")
        box.insert("1.0", text)
        box.configure(state="disabled")

    @staticmethod
    def export(text, name):
        path = filedialog.asksaveasfilename(initialfile=name, defaultextension=Path(name).suffix)
        if path:
            try:
                Path(path).write_text(text, encoding="utf-8")
            except OSError as error:
                messagebox.showerror("Fayl saxlanmadı", str(error))

    def library(self, pane):
        catalog = learning.lessons()
        query = self.entry(pane, "Mövzu və ya fənn axtar")
        selector = ttk.Combobox(pane, state="readonly")
        selector.pack(fill="x", pady=(0, 7))
        content = ttk.Frame(pane)
        content.pack(fill="both", expand=True, pady=(6, 0))
        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=2, minsize=220)
        content.rowconfigure(0, weight=1)
        lesson = ttk.Frame(content)
        lesson.grid(row=0, column=0, sticky="nsew", padx=(0, 13))
        practice = ttk.Frame(content, padding=12, style="Practice.TFrame")
        practice.grid(row=0, column=1, sticky="nsew")
        ttk.Label(lesson, text="Dərsin izahı", style="Section.TLabel").pack(anchor="w")
        text = self.output(lesson)
        ttk.Label(practice, text="Biliyini yoxla", style="PracticeHeading.TLabel").pack(anchor="w")
        question = tk.StringVar()
        ttk.Label(practice, textvariable=question, wraplength=195, style="Practice.TLabel").pack(
            anchor="w", fill="x", pady=(9, 8)
        )
        attempt = self.entry(practice, "Cavabın")
        result = tk.StringVar()
        ttk.Label(practice, textvariable=result, wraplength=195, style="Practice.TLabel").pack(
            anchor="w", fill="x", pady=(3, 0)
        )
        visible = []

        def selected(event=None):
            item = visible[selector.current()] if selector.current() >= 0 else None
            self.show(text, item["text"] if item else "Uyğun dərs tapılmadı.")
            question.set(item["question"] if item else "")
            result.set("")
            attempt.delete(0, "end")

        def filter_catalog(event=None):
            term = query.get().strip().casefold()
            visible[:] = [item for item in catalog if term in
                          (item["subject"] + " " + item["title"] + " " + item["text"]).casefold()]
            selector["values"] = [f'{item["subject"]} · {item["title"]}' for item in visible]
            if visible:
                selector.current(0)
            else:
                selector.set("")
            selected()

        def check():
            if selector.current() < 0 or not attempt.get().strip():
                return
            item = visible[selector.current()]
            answer = "".join(attempt.get().casefold().split())
            correct = answer == "".join(item["answer"].casefold().split())
            result.set(("Düzdür. " if correct else "Bir daha yoxla. ") + item["explanation"])

        selector.bind("<<ComboboxSelected>>", selected)
        query.bind("<KeyRelease>", filter_catalog)
        attempt.bind("<Return>", lambda event: check())
        ttk.Button(practice, text="Cavabı yoxla", command=check, style="Primary.TButton").pack(
            anchor="w", pady=(6, 0)
        )
        filter_catalog()

    def flashcards(self, pane):
        question = self.entry(pane, "Yeni kartın sualı")
        answer = self.entry(pane, "Yeni kartın cavabı")
        prompt = tk.StringVar()
        attempt = self.entry(pane, "Yaddaşdan cavab yaz")
        displayed = tk.StringVar()
        count = tk.StringVar()
        ttk.Label(pane, textvariable=prompt, wraplength=550).pack(anchor="w")
        ttk.Label(pane, textvariable=displayed, wraplength=550).pack(anchor="w", pady=7)

        def refresh():
            due = [card for card in self.cards if card["due"] <= learning.now_ms()]
            self.current = min(due, key=lambda card: card["due"], default=None)
            prompt.set(self.current["q"] if self.current else "Vaxtı çatmış kart yoxdur.")
            count.set(f"Təkrar vaxtı çatan {len(due)} / {len(self.cards)} kart")
            displayed.set("")
            attempt.delete(0, "end")

        def add():
            q, a = question.get().strip(), answer.get().strip()
            if not (0 < len(q) <= 4000 and 0 < len(a) <= 4000 and len(self.cards) < 10000):
                messagebox.showerror("Kart əlavə edilmədi", "Sualı və cavabı daxil edin.")
                return
            self.cards.append(dict(q=q, a=a, due=learning.now_ms(), interval=0))
            question.delete(0, "end")
            answer.delete(0, "end")
            refresh()

        def reveal():
            if self.current:
                displayed.set(self.current["a"])

        def rate(recalled):
            if self.current and displayed.get():
                learning.schedule(self.current, recalled, learning.now_ms())
                refresh()

        def load():
            path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
            if not path:
                return
            try:
                with open(path, "rb") as source:
                    data = source.read(2_000_001)
                if len(data) > 2_000_000:
                    raise ValueError("Fayl 2 MB həddini keçir.")
                cards = learning.parse_cards(data.decode("utf-8"))
            except (OSError, ValueError, RecursionError) as error:
                messagebox.showerror("Kartlar açılmadı", str(error))
                return
            if self.cards and not messagebox.askyesno("Kartları əvəz et", "Cari kartlar əvəz edilsin?"):
                return
            self.cards = cards
            refresh()

        def save():
            text = json.dumps(self.cards, ensure_ascii=False)
            if len(text.encode("utf-8")) > 2_000_000:
                messagebox.showerror("Kartlar saxlanmadı", "Kart faylı 2 MB həddini keçir.")
                return
            self.export(text, "relife-cards.json")

        self.actions(pane, ("Kart əlavə et", add), ("Cavabı göstər", reveal),
                     ("Təkrar et", lambda: rate(False)), ("Bildim", lambda: rate(True)))
        self.actions(pane, ("Kartları aç", load), ("Kartları ixrac et", save), ("Yenilə", refresh))
        ttk.Label(pane, textvariable=count).pack(anchor="w")
        refresh()

    def teacher(self, pane):
        subject = self.entry(pane, "Fənn və sinif")
        topic = self.entry(pane, "Dərsin mövzusu")
        objective = self.entry(pane, "Təlim nəticəsi")
        duration = self.entry(pane, "Müddət (dəqiqə)", "45")
        result = self.output(pane)

        def plan():
            try:
                self.show(result, learning.lesson_plan(subject.get(), "", topic.get(), objective.get(),
                                                      int(duration.get())))
            except ValueError as error:
                messagebox.showerror("Plan hazırlanmadı", str(error))

        def worksheet():
            catalog = [lesson for lesson in learning.lessons()
                       if not subject.get().strip() or subject.get().casefold().strip() in lesson["subject"].casefold()]
            if not catalog:
                messagebox.showinfo("İş vərəqi", "Daxil etdiyin fənn üzrə hazır sual tapılmadı.")
                return
            title = topic.get().strip() or "Təkrar sualları"
            questions = "\n\n".join(f'{index}. {item["question"]}\nCavab: ____________________'
                                    for index, item in enumerate(catalog, 1))
            answers = "\n".join(f'{index}. {item["answer"]} — {item["explanation"]}'
                                for index, item in enumerate(catalog, 1))
            self.show(result, f"{title}\n\n{questions}")
            if messagebox.askyesno("İş vərəqi", "Cavab açarını ayrıca fayla ixrac edək?"):
                self.export(f"{title} · Cavab açarı\n\n{answers}", "cavab-acari.txt")

        self.actions(pane, ("Planı hazırla", plan), ("İş vərəqi hazırla", worksheet),
                     ("Mətn kimi ixrac et", lambda: self.export(result.get("1.0", "end-1c"), "ders-materiali.txt")))

    def science(self, pane):
        formulas = ttk.Combobox(pane, state="readonly", values=list(learning.LABS))
        formulas.pack(fill="x", pady=(0, 7))
        formulas.current(0)
        hint = tk.StringVar(value=learning.LABS[formulas.get()][0])
        ttk.Label(pane, textvariable=hint).pack(anchor="w")
        values = self.entry(pane, "Qiymətlər")
        result = tk.StringVar()

        def calculate():
            try:
                result.set(f"Nəticə  {learning.calculate(formulas.get(), values.get()):.12g}")
            except ValueError as error:
                result.set(str(error))

        def changed(event):
            hint.set(learning.LABS[formulas.get()][0])
            result.set("")

        formulas.bind("<<ComboboxSelected>>", changed)
        values.bind("<Return>", lambda event: calculate())
        self.actions(pane, ("Hesabla", calculate))
        ttk.Label(pane, textvariable=result).pack(anchor="w")

    def planner(self, pane):
        subject = self.entry(pane, "Fənn")
        task = self.entry(pane, "Tapşırıq və ya öyrənmə məqsədi")
        tasks = tk.Listbox(pane, activestyle="dotbox", selectmode="browse")
        tasks.pack(fill="both", expand=True, pady=(2, 7))
        records = []

        def add():
            field, title = subject.get().strip(), task.get().strip()
            if not field or not title:
                return
            records.append([field, title, False])
            tasks.insert("end", f"□ {field} · {title}")
            task.delete(0, "end")

        def complete():
            selection = tasks.curselection()
            if not selection:
                return
            index, = selection
            field, title, done = records[index]
            records[index][2] = not done
            tasks.delete(index)
            marker = "□" if done else "✓"
            tasks.insert(index, f"{marker} {field} · {title}")
            tasks.selection_set(index)

        def export():
            lines = ["Günün təhsil planı", ""]
            lines.extend(f'{"[x]" if done else "[ ]"} {field} · {title}' for field, title, done in records)
            self.export("\n".join(lines), "gunun-plani.txt")

        task.bind("<Return>", lambda event: add())
        self.actions(pane, ("Əlavə et", add), ("Tamamlandı / geri al", complete), ("Planı ixrac et", export))

    def notes(self, pane):
        ttk.Label(pane, text="Qeyd dəftəri").pack(anchor="w")
        text = self.output(pane, height=12, editable=True)
        self.actions(pane, ("Qeydləri ixrac et", lambda: self.export(text.get("1.0", "end-1c"), "qeyd.txt")))

    def focus(self, pane):
        target = self.entry(pane, "Bu sessiyada hansı işi görəcəksən?")
        work = self.entry(pane, "Məşq müddəti (dəqiqə)", "25")
        rest = self.entry(pane, "Fasilə müddəti (dəqiqə)", "5")
        status = tk.StringVar()
        ttk.Label(pane, textvariable=status, wraplength=550).pack(anchor="w", pady=10)

        def stop():
            if self.focus_timer is not None:
                self.root.after_cancel(self.focus_timer)
                self.focus_timer = None
            status.set("")

        def tick(deadline, label):
            remaining = max(0, (deadline - learning.now_ms() + 999) // 1000)
            status.set(f"{label} · {remaining // 60}:{remaining % 60:02d}" if remaining else
                       f"{label} · Sessiya tamamlandı.")
            self.focus_timer = self.root.after(500, tick, deadline, label) if remaining else None

        def begin(field, label):
            try:
                minutes = int(field.get())
                if not 1 <= minutes <= 180:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Müddət", "1–180 dəqiqə arası tam ədəd yazın.")
                return
            stop()
            tick(learning.now_ms() + minutes * 60000, label)

        self.actions(pane, ("Başla", lambda: begin(work, target.get().strip() or "Fokus")),
                     ("Fasilə", lambda: begin(rest, "Fasilə")), ("Dayandır", stop))

    def help(self, pane):
        self.help_pane = pane
        text = self.output(pane)
        self.show(text, "Başla menyusu vasitəsilə proqramları aç. Super+E fayl menecerini açır. "
                  "Alt+Tab açıq pəncərələr arasında keçir. Ctrl+ və Ctrl− təhsil mərkəzinin mətn ölçüsünü dəyişir.\n\n"
                  "Kitabxana və laboratoriya internetsiz işləyir. Bir dərsi oxu, sualı cavablandır "
                  "və səhv etdiyin mövzunu Təkrar bölməsində karta çevir.\n\n"
                  "İşini bitirəndə faylın saxlandığı yeri yoxla. RAM sessiyasındakı fayllar "
                  "yenidən başlatdıqda silinir. Kompüteri Başla → Söndür vasitəsilə bağla.")

    def ai(self, pane):
        if not shutil.which("firefox-esr"):
            ttk.Label(pane, text="Onlayn AI üçün Firefox ESR olan ReLife Education buraxılışını aç.",
                      wraplength=550).pack(anchor="w")
            return
        ttk.Label(pane, text="Bu xidmətlər internet bağlantısı tələb edir. Açılarkən dərslər və "
                  "qeydlər xidmətə ötürülmür.", wraplength=550).pack(anchor="w", pady=(0, 9))
        for name, url in (("ChatGPT", "https://chatgpt.com/"), ("Claude", "https://claude.ai/"),
                          ("Gemini", "https://gemini.google.com/")):
            self.actions(pane, (name, lambda name=name, url=url: self.open_provider(name, url)))

    @staticmethod
    def open_provider(name, url):
        if messagebox.askyesno("Onlayn xidmət", f"{name} Firefox-da açılsın?"):
            try:
                subprocess.Popen(["relife-firefox", url])
            except OSError as error:
                messagebox.showerror("Xidmət açılmadı", str(error))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--help-page", action="store_true")
    args = parser.parse_args()
    root = tk.Tk(className="RelifeEducation")
    icon_path = Path("/usr/share/icons/relife/education.png")
    if icon_path.is_file():
        icon = tk.PhotoImage(file=icon_path)
        root.iconphoto(True, icon)
    app = Education(root)
    if args.help_page:
        app.tabs.select(app.help_pane)
    root.mainloop()
