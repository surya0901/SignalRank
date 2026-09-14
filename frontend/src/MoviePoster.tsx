import { useState } from "react";
import { Movie, title } from "./engine";
import posterUrls from "./posters.json";

export default function MoviePoster({ movie }: { movie: Movie }) {
  const [failed, setFailed] = useState(false);
  const url = (posterUrls as Record<string, string>)[movie.id];
  if (!url || failed)
    return (
      <div className="poster-placeholder">
        <span>SignalRank cinema</span>
        <strong>{title(movie)}</strong>
        <small>Poster unavailable</small>
      </div>
    );
  return (
    <img src={url} alt={`${title(movie)} poster`} loading="lazy"
      referrerPolicy="no-referrer" onError={() => setFailed(true)} />
  );
}
