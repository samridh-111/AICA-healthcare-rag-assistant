
export default function Header() {
  return (
    <header className="bg-surface dark:bg-surface-dim fixed top-0 right-0 left-64 h-16 border-b border-on-surface/5 flex justify-between items-center px-lg z-10">
      <div className="font-headline-md text-headline-md text-on-surface flex items-center gap-md">
        <span className="">Patient Insights</span>
      </div>
      <nav className="hidden lg:flex items-center gap-lg h-full">
        <a className="h-full flex items-center font-label-md text-label-md hover:text-primary transition-colors cursor-pointer active:opacity-70 text-primary border-b-2 border-primary pb-1 pt-1" href="#">Overview</a>
        <a className="h-full flex items-center font-label-md text-label-md hover:text-primary transition-colors cursor-pointer active:opacity-70 text-on-surface-variant" href="#">Vitals</a>
        <a className="h-full flex items-center font-label-md text-label-md hover:text-primary transition-colors cursor-pointer active:opacity-70 text-on-surface-variant" href="#">History</a>
        <a className="h-full flex items-center font-label-md text-label-md hover:text-primary transition-colors cursor-pointer active:opacity-70 text-on-surface-variant" href="#">Meds</a>
      </nav>
      <div className="flex items-center gap-md text-on-surface-variant">
        <button className="p-sm rounded-full hover:bg-surface-container transition-colors focus:outline-none">
          <span className="material-symbols-outlined">notifications</span>
        </button>
        <button className="p-sm rounded-full hover:bg-surface-container transition-colors focus:outline-none">
          <span className="material-symbols-outlined" data-weight="fill">account_circle</span>
        </button>
      </div>
    </header>
  );
}
