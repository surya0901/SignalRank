const paths: Record<string, string> = {
  home: "m3 10 9-7 9 7v10H3z M9 20v-7h6v7",
  explore: "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20 M16 8l-3 5-5 3 3-5z",
  sliders: "M3 6h8m4 0h6M3 12h3m4 0h11M3 18h12m4 0h2M11 3v6M6 9v6M15 15v6",
  chart: "M4 20V10h4v10 M10 20V4h4v16 M16 20V7h4v13",
  bookmark: "M6 3h12v18l-6-4-6 4z",
  heart:
    "M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8z",
  star: "m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2-5.6-3-5.6 3 1.1-6.2L3 9.6l6.2-.9z",
  search: "M10.5 18a7.5 7.5 0 1 0 0-15 7.5 7.5 0 0 0 0 15 M16 16l5 5",
  arrow: "M4 12h16m-6-6 6 6-6 6",
  chevron: "m9 5 7 7-7 7",
  close: "m6 6 12 12M6 18 18 6",
  user: "M16 7a4 4 0 1 0-8 0 4 4 0 0 0 8 0 M4 21v-3a8 8 0 0 1 16 0v3z",
  model: "m12 2 9 5-9 5-9-5z M3 12l9 5 9-5M3 17l9 5 9-5",
  check: "m5 12 4 4L19 6",
  reset: "M3 10a9 9 0 1 1 1 7 M3 3v7h7",
  info: "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20 M12 11v6M12 7v1",
};
export default function Icon({
  name,
  size = 20,
}: {
  name: string;
  size?: number;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={paths[name] || paths.info} />
    </svg>
  );
}
