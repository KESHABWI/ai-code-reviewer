export function LogoMark({ size = 36 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="Codelight logo"
    >
      <defs>
        <linearGradient id="codelightGrad" x1="4" y1="2" x2="60" y2="62" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#2AA7FF" />
          <stop offset="0.55" stopColor="#0071E3" />
          <stop offset="1" stopColor="#5E5CE6" />
        </linearGradient>
        <linearGradient id="codelightSheen" x1="32" y1="2" x2="32" y2="30" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#FFFFFF" stopOpacity="0.35" />
          <stop offset="1" stopColor="#FFFFFF" stopOpacity="0" />
        </linearGradient>
      </defs>
      <rect x="2" y="2" width="60" height="60" rx="17" fill="url(#codelightGrad)" />
      <rect x="2" y="2" width="60" height="28" rx="17" fill="url(#codelightSheen)" />
      <path
        d="M24.5 21 14 32l10.5 11"
        stroke="white"
        strokeWidth="4.4"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.55"
      />
      <path
        d="M39.5 21 50 32 39.5 43"
        stroke="white"
        strokeWidth="4.4"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.55"
      />
      <path
        d="M23 34.5 29 40.5 41.5 25.5"
        stroke="white"
        strokeWidth="5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function LogoLockup({ size = 30 }: { size?: number }) {
  return (
    <div className="flex items-center gap-2.5 select-none">
      <LogoMark size={size} />
      <span className="font-display font-semibold tracking-[-0.02em] text-[1.15rem] text-ink">
        Codelight
      </span>
    </div>
  );
}
