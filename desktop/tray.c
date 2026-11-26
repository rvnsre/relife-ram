/* A small XEmbed status control for the IceWM tray. */
#define _POSIX_C_SOURCE 200809L
#include <X11/Xatom.h>
#include <X11/XKBlib.h>
#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <glob.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

enum { WIDTH = 128, HEIGHT = 34 };
static Display *display;
static Window window, root;
static GC gc;
static XFontStruct *font;

static void run(const char *program, const char *argument)
{
    if (fork() == 0) {
        close(ConnectionNumber(display));
        execlp(program, program, argument, (char *)NULL);
        _exit(127);
    }
}

static int network_up(void)
{
    glob_t paths;
    int up = 0;
    if (glob("/sys/class/net/*/operstate", 0, NULL, &paths) == 0) {
        for (size_t i = 0; i < paths.gl_pathc; i++) {
            if (strcmp(paths.gl_pathv[i], "/sys/class/net/lo/operstate") == 0)
                continue;
            FILE *file = fopen(paths.gl_pathv[i], "r");
            if (file) {
                char state[12];
                if (fgets(state, sizeof state, file) && strcmp(state, "up\n") == 0)
                    up = 1;
                fclose(file);
            }
        }
    }
    globfree(&paths);
    return up;
}

static int battery_level(void)
{
    glob_t paths;
    int level = -1;
    if (glob("/sys/class/power_supply/BAT*/capacity", 0, NULL, &paths) == 0 && paths.gl_pathc) {
        FILE *file = fopen(paths.gl_pathv[0], "r");
        if (file) {
            if (fscanf(file, "%d", &level) != 1)
                level = -1;
            fclose(file);
        }
    }
    globfree(&paths);
    return level >= 0 && level <= 100 ? level : -1;
}

static void clock_line(const char *text, int y)
{
    int length = (int)strlen(text);
    int width = font ? XTextWidth(font, text, length) : length * 6;
    XDrawString(display, window, gc, 93 - width / 2, y, text, length);
}

static void paint(void)
{
    XWindowAttributes bounds;
    XGetWindowAttributes(display, window, &bounds);
    int center = bounds.height / 2;
    time_t now = time(NULL);
    struct tm local;
    localtime_r(&now, &local);
    char clock[12], day[16];
    strftime(clock, sizeof clock, "%H:%M", &local);
    strftime(day, sizeof day, "%d.%m.%Y", &local);
    XClearWindow(display, window);
    XSetLineAttributes(display, gc, 1, LineSolid, CapRound, JoinRound);
    XDrawArc(display, window, gc, 6, center-5, 16, 13, 34*64, 112*64);
    XDrawArc(display, window, gc, 9, center-2, 10, 8, 36*64, 108*64);
    XFillRectangle(display, window, gc, 13, center+1, 2, 2);
    if (!network_up())
        XDrawLine(display, window, gc, 6, center-7, 21, center+6);
    XPoint speaker[] = {{25,center-2}, {29,center-2}, {33,center-6}, {33,center+6},
                        {29,center+2}, {25,center+2}, {25,center-2}};
    XDrawLines(display, window, gc, speaker, 7, CoordModeOrigin);
    XDrawArc(display, window, gc, 29, center-6, 10, 12, -56*64, 112*64);
    XkbStateRec keyboard;
    const char *language = XkbGetState(display, XkbUseCoreKbd, &keyboard) == Success &&
                           keyboard.group == 1 ? "AZ" : "EN";
    XDrawString(display, window, gc, 42, center+4, language, 2);
    XDrawRectangle(display, window, gc, 57, center-5, 10, 10);
    XFillRectangle(display, window, gc, 68, center-2, 2, 5);
    int charge = battery_level();
    if (charge >= 0)
        XFillRectangle(display, window, gc, 59, center-3, (unsigned int)(charge * 8 / 100), 7);
    else
        XDrawLine(display, window, gc, 60, center, 64, center);
    clock_line(clock, center-3);
    clock_line(day, center+10);
    XDrawLine(display, window, gc, WIDTH-7, 0, WIDTH-7, bounds.height);
    XFlush(display);
}

int main(void)
{
    signal(SIGCHLD, SIG_IGN);
    display = XOpenDisplay(NULL);
    if (!display)
        return 1;
    root = DefaultRootWindow(display);
    int screen = DefaultScreen(display);
    char selection[40];
    snprintf(selection, sizeof selection, "_NET_SYSTEM_TRAY_S%d", screen);
    Atom tray = XInternAtom(display, selection, False);
    Window owner = None;
    for (int attempt = 0; attempt < 100 && owner == None; attempt++) {
        owner = XGetSelectionOwner(display, tray);
        if (owner == None)
            nanosleep(&(struct timespec){.tv_nsec = 100000000}, NULL);
    }
    if (owner == None)
        return 1;
    XColor color, exact;
    unsigned long background = BlackPixel(display, screen);
    if (XAllocNamedColor(display, DefaultColormap(display, screen), "#101010", &color, &exact))
        background = color.pixel;
    window = XCreateSimpleWindow(display, root, 0, 0, WIDTH, HEIGHT, 0, background, background);
    XStoreName(display, window, "ReLife");
    XSizeHints hints = {.flags = PMinSize | PMaxSize, .min_width = WIDTH, .max_width = WIDTH,
                        .min_height = HEIGHT, .max_height = HEIGHT};
    XSetWMNormalHints(display, window, &hints);
    Atom embed = XInternAtom(display, "_XEMBED_INFO", False);
    unsigned long properties[] = {0, 1};
    XChangeProperty(display, window, embed, embed, 32, PropModeReplace, (unsigned char *)properties, 2);
    XSelectInput(display, window, ExposureMask | StructureNotifyMask | ButtonPressMask);
    XEvent request = {0};
    request.xclient.type = ClientMessage;
    request.xclient.window = owner;
    request.xclient.message_type = XInternAtom(display, "_NET_SYSTEM_TRAY_OPCODE", False);
    request.xclient.format = 32;
    request.xclient.data.l[0] = CurrentTime;
    request.xclient.data.l[2] = window;
    XSendEvent(display, owner, False, NoEventMask, &request);
    gc = XCreateGC(display, window, 0, NULL);
    XSetForeground(display, gc, WhitePixel(display, screen));
    font = XLoadQueryFont(display, "5x7");
    if (font)
        XSetFont(display, gc, font->fid);
    else
        font = XQueryFont(display, XGContextFromGC(gc));
    XFlush(display);
    struct pollfd connection = {.fd = ConnectionNumber(display), .events = POLLIN};
    for (;;) {
        while (XPending(display)) {
            XEvent event;
            XNextEvent(display, &event);
            if (event.type == DestroyNotify)
                return 0;
            if (event.type != ButtonPress || event.xbutton.button != Button1)
                continue;
            int x = event.xbutton.x;
            if (x < 23)
                run("relife-desktop", "network");
            else if (x < 40)
                run("relife-sound", NULL);
            else if (x >= 55 && x < 72)
                run("relife-desktop", "system");
            else if (x >= 72 && x < WIDTH-7)
                run("relife-desktop", "calendar");
            else if (x >= WIDTH-7) {
                Atom show = XInternAtom(display, "_NET_SHOWING_DESKTOP", False);
                Atom kind;
                int format;
                unsigned long count, rest;
                unsigned char *data = NULL;
                XGetWindowProperty(display, root, show, 0, 1, False, XA_CARDINAL, &kind,
                                   &format, &count, &rest, &data);
                XEvent toggle = {0};
                toggle.xclient.type = ClientMessage;
                toggle.xclient.window = root;
                toggle.xclient.message_type = show;
                toggle.xclient.format = 32;
                toggle.xclient.data.l[0] = !data || !count || !*(unsigned long *)data;
                if (data)
                    XFree(data);
                XSendEvent(display, root, False, SubstructureNotifyMask | SubstructureRedirectMask, &toggle);
            }
        }
        paint();
        poll(&connection, 1, 3000);
    }
}
