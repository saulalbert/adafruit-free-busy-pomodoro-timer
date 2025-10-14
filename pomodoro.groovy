/*
pomodoro_timer.groovy — Freeplane Pomodoro UI with BLE sync
CC0-1.0 (Public Domain). https://creativecommons.org/publicdomain/zero/1.0/

INSTALL / SETUP
1) Save this script anywhere (e.g. your Freeplane scripts folder) and run it.
2) macOS: install Python + bleak on your system Python:
     python3 -m pip install bleak
3) Copy the Mac BLE helper to a path you control, e.g.:
     ~/pomodoro-display/mac_pomodoro_ble.py
4) Edit the CONFIG section below to point at your Python and script path.
5) Feather must be flashed with the matching code.py from this repo.

COMMANDS SENT:
  START <seconds>, PAUSE, RESUME, STOP
*/

// ---------------------------
// CONFIG (edit these)
// ---------------------------
def CONFIG = [
    enableBLE    : true,              // set false to disable external calls
    pythonPaths  : [
        "/usr/bin/python3",
        "/opt/homebrew/bin/python3",
        "/opt/anaconda3/bin/python3"
    ],                                // will try in order until one works
    bleScriptPath: System.getProperty("user.home") + "/pomodoro-display/mac_pomodoro_ble.py",
    logFile      : System.getProperty("user.home") + "/pomodoro-display/ble_log.txt",
]

// ---------------------------
// Imports
// ---------------------------
import groovy.swing.SwingBuilder
import groovy.transform.SourceURI

import java.awt.FlowLayout as FL
import javax.swing.BoxLayout as BXL
import javax.swing.JFrame
import javax.swing.JDialog
import javax.swing.JLabel
import javax.swing.JButton
import javax.swing.JCheckBox
import java.applet.Applet
import java.applet.AudioClip

// ---------------------------
// BLE helper
// ---------------------------
static void _appendLog(File f, String line) {
    try {
        f.parentFile?.mkdirs()
        f << (line + "\n")
    } catch (ignored) {}
}

static String _resolvePython(List<String> candidates, File log) {
    for (p in candidates) {
        try {
            def pb = new ProcessBuilder(p, "-V")
            pb.redirectErrorStream(true)
            def proc = pb.start()
            def out = proc.inputStream.text
            proc.waitFor()
            if (proc.exitValue() == 0 && out?.toLowerCase()?.contains("python")) {
                _appendLog(log, "Using Python: ${p} (${out.trim()})")
                return p
            }
        } catch (ignored) {}
    }
    _appendLog(log, "No working python3 found in candidates.")
    return null
}

static void runBleCommand(Map CONFIG, String cmd) {
    if (!CONFIG.enableBLE) return
    File log = new File(CONFIG.logFile)
    _appendLog(log, "Running BLE command: ${cmd}")

    File script = new File(CONFIG.bleScriptPath)
    if (!script.exists()) {
        _appendLog(log, "BLE script not found: ${script.absolutePath}")
        return
    }

    def py = _resolvePython(CONFIG.pythonPaths, log)
    if (py == null) {
        _appendLog(log, "Aborting; no python3 available.")
        return
    }

    try {
        def pb = new ProcessBuilder(py, script.absolutePath, cmd)
        pb.redirectErrorStream(true)
        def proc = pb.start()
        proc.inputStream.eachLine { _appendLog(log, "BLE: ${it}") }
        def code = proc.waitFor()
        _appendLog(log, "Process exit code: ${code}")
    } catch (Exception e) {
        _appendLog(log, "BLE exception: ${e.message}")
    }
}

// ---------------------------
// Pomodoro class (UI & logic)
// ---------------------------
class PomodoroTimer {
    @SourceURI
    URI scriptUri

    // Durations (seconds)
    static final int WORK_DURATION  = 25 * 60
    static final int SHORT_BREAK    = 5  * 60
    static final int LONG_BREAK     = 15 * 60
    static final int PERIOD = 1

    // Attribute keys
    static final String NODE_MINUTES_ATTR = "Who"
    static final String ROOT_COUNT_SUFFIX = "_count"

    int remainingTime = WORK_DURATION
    int pomodoroCount = 0
    boolean running = false
    boolean onBreak = false

    javax.swing.Timer swingTimer
    def node
    JLabel timeLabel
    JLabel statusLabel
    JButton controlButton
    JButton closeButton
    JButton skipBreakButton
    JCheckBox alwaysOnTop
    JDialog dialog
    Map CONFIG

    PomodoroTimer(
        nodeIn, JLabel timeLabel, JLabel statusLabel,
        JButton controlButton, JButton closeButton,
        JButton skipBreakButton, JCheckBox alwaysOnTop,
        JDialog dialog, Map CONFIG
    ) {
        node = nodeIn
        this.timeLabel = timeLabel
        this.statusLabel = statusLabel
        this.controlButton = controlButton
        this.closeButton = closeButton
        this.skipBreakButton = skipBreakButton
        this.alwaysOnTop = alwaysOnTop
        this.dialog = dialog
        this.CONFIG = CONFIG

        updateTimeDisplay()
        updateStatusDisplay("Work Session (Pomodoro 1 of 4)")
        updateButtonText()

        swingTimer = new javax.swing.Timer(1000, { e -> update() } as java.awt.event.ActionListener)
        swingTimer.setRepeats(true)
        swingTimer.start()
    }

    void startSession() {
        running = true
        updateButtonText()
        runBleCommand(CONFIG, "START ${remainingTime}")
    }

    void pauseSession() {
        running = false
        updateButtonText()
        runBleCommand(CONFIG, "PAUSE")
    }

    void toggleSession() {
        if (onBreak) return
        if (running) pauseSession() else startSession()
    }

    void endSession() {
        running = false
        playSound()
        runBleCommand(CONFIG, "STOP")

        if (!onBreak) {
            pomodoroCount++
            accumulateTime(WORK_DURATION)
            if (pomodoroCount % 4 == 0) {
                startBreak(LONG_BREAK, "Long Break (after 4 Pomodoros)")
            } else {
                int num = (pomodoroCount % 4) + 1
                startBreak(SHORT_BREAK, "Short Break (next Pomodoro ${num} of 4)")
            }
        } else {
            startWork()
        }
    }

    void startWork() {
        onBreak = false
        remainingTime = WORK_DURATION
        int cycleNum = (pomodoroCount % 4) + 1
        updateStatusDisplay("Work Session (Pomodoro ${cycleNum} of 4)")
        running = false
        updateButtonText()
    }

    void startBreak(int duration, String label) {
        onBreak = true
        remainingTime = duration
        updateStatusDisplay(label)
        startSession()               // auto-run breaks
        updateButtonText()
        runBleCommand(CONFIG, "START ${remainingTime}")
    }

    void skipBreak() {
        if (onBreak) {
            runBleCommand(CONFIG, "STOP")
            startWork()
        }
    }

    void update() {
        if (!running) return
        if (remainingTime > 0) {
            remainingTime -= PERIOD
            updateTimeDisplay()
        } else {
            endSession()
        }
    }

    void updateTimeDisplay() {
        timeLabel.setText(secondToString(remainingTime))
        updateButtonText()
    }

    void updateStatusDisplay(String text) {
        statusLabel.setText(text)
    }

    void updateButtonText() {
        if (running) {
            if (onBreak) {
                controlButton.setText("Running")
                controlButton.setEnabled(false)
            } else {
                controlButton.setText("Pause")
                controlButton.setEnabled(true)
            }
        } else {
            controlButton.setEnabled(true)
            boolean atWorkStart  = !onBreak && remainingTime == WORK_DURATION
            boolean atBreakStart = onBreak && (remainingTime == SHORT_BREAK || remainingTime == LONG_BREAK)
            controlButton.setText( (atWorkStart || atBreakStart) ? "Start" : "Resume" )
        }
    }

    static String secondToString(int s) {
        int m = s.intdiv(60)
        int r = s % 60
        return String.format("%02d:%02d", m, r)
    }

    static int getAttrInt(def n, String key) {
        def v = n.getAttributes().get(key)
        if (v == null) return 0
        try {
            return (v instanceof Number) ? v.intValue() : Integer.parseInt(v.toString())
        } catch (ignored) { return 0 }
    }

    void accumulateTime(int sessionSeconds) {
        int minutes = sessionSeconds.intdiv(60)
        node[NODE_MINUTES_ATTR] = getAttrInt(node, NODE_MINUTES_ATTR) + minutes
        def root = node.getMap().getRootNode()
        def today = new Date().format("yyyy-MM-dd")
        root[today]                      = getAttrInt(root, today) + minutes
        root[today + ROOT_COUNT_SUFFIX]  = getAttrInt(root, today + ROOT_COUNT_SUFFIX) + 1
    }

    void playSound() {
        try {
            File scriptDir = new File(scriptUri).parentFile
            File soundFile = new File(scriptDir, "end.wav")
            if (soundFile.exists()) {
                AudioClip sound = Applet.newAudioClip(soundFile.toURL())
                sound.play()
            } else {
                java.awt.Toolkit.getDefaultToolkit().beep()
            }
        } catch (Exception ignored) {
            java.awt.Toolkit.getDefaultToolkit().beep()
        }
    }

    void shutdown() {
        try { if (swingTimer && swingTimer.isRunning()) swingTimer.stop() } catch (ignored) {}
        if (dialog && dialog.isDisplayable()) dialog.dispose()
        runBleCommand(CONFIG, "STOP")
    }
}

// ---------- UI ----------
def s = new SwingBuilder()

JLabel nodeLabel = new JLabel("")
JLabel timeLabel = new JLabel("25:00")
JLabel statusLabel = new JLabel("Work Session")
JButton controlButton = new JButton("Start")
JButton closeButton = new JButton("Close")
JButton skipBreakButton = new JButton("Skip Break")
JCheckBox alwaysOnTop = new JCheckBox("Always on top", false)

def dial = s.dialog(
        title: "Pomodoro Timer",
        modal: false,
        defaultCloseOperation: JFrame.DISPOSE_ON_CLOSE,
        pack: true,
        show: true
) {
    panel {
        boxLayout(axis: BXL.Y_AXIS)
        panel { flowLayout(alignment: FL.CENTER); widget(statusLabel) }
        panel { flowLayout(alignment: FL.CENTER); widget(timeLabel) }
        panel {
            flowLayout(alignment: FL.CENTER)
            widget(controlButton); widget(skipBreakButton); widget(closeButton)
        }
        panel { flowLayout(alignment: FL.CENTER); widget(alwaysOnTop) }
    }
}

PomodoroTimer model = new PomodoroTimer(
    node, timeLabel, statusLabel, controlButton, closeButton,
    skipBreakButton, alwaysOnTop, dial, CONFIG
)

controlButton.addActionListener { model.toggleSession() }
closeButton.addActionListener   { model.shutdown() }
skipBreakButton.addActionListener { model.skipBreak() }
alwaysOnTop.addActionListener { dial.setAlwaysOnTop(alwaysOnTop.isSelected()) }

// Optional: auto-start the first Pomodoro
model.startSession()

