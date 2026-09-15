import { Clock3, Pause, Play } from "lucide-react";
import { useState } from "react";
export function TemporalControls() {
  const [playing, setPlaying] = useState(false);
  return (
    <section className="time-controls" aria-label="Generated time controls">
      <button
        type="button"
        aria-label={playing ? "Pause generated replay" : "Play generated replay"}
        aria-pressed={playing}
        onClick={() => setPlaying(!playing)}
      >
        {playing ? <Pause size={16} /> : <Play size={16} />}
      </button>
      <Clock3 size={15} />
      <span>23:00</span>
      <input type="range" min="0" max="60" defaultValue="60" aria-label="Generated time window" />
      <span>00:00 UTC</span>
      <strong>60 min</strong>
    </section>
  );
}
