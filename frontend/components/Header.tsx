import { LogoLockup } from "./Logo";

export function Header() {
  return (
    <header className="glass sticky top-0 z-30 border-b border-hairline/60">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-5 py-3.5 sm:px-8">
        <LogoLockup size={30} />
        <span className="hidden rounded-full bg-canvas px-3 py-1 text-[0.75rem] font-medium text-subink sm:inline">
          PR-style reviews, on demand
        </span>
      </div>
    </header>
  );
}
