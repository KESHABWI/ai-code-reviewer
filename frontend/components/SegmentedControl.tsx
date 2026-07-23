"use client";

export function SegmentedControl<T extends string>({
  options,
  value,
  onChange,
}: {
  options: { value: T; label: string }[];
  value: T;
  onChange: (v: T) => void;
}) {
  const activeIndex = options.findIndex((o) => o.value === value);

  return (
    <div className="relative inline-flex w-full max-w-full rounded-xl bg-[#efeff1] p-1 sm:w-auto">
      <div
        className="absolute inset-y-1 rounded-lg bg-white shadow-[0_1px_3px_rgba(0,0,0,0.12)] transition-all duration-300 ease-out"
        style={{
          width: `calc(${100 / options.length}% - 4px)`,
          left: `calc(${(100 / options.length) * activeIndex}% + 2px)`,
        }}
      />
      {options.map((opt) => (
        <button
          key={opt.value}
          onClick={() => onChange(opt.value)}
          className={`relative z-10 flex-1 whitespace-nowrap rounded-lg px-4 py-1.5 text-[0.83rem] font-medium transition-colors duration-200 sm:flex-none ${
            value === opt.value ? "text-ink" : "text-subink hover:text-ink"
          }`}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
