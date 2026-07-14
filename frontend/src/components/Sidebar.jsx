import { useRef } from 'react';

export default function Sidebar({ onIngest, onUpload, onClear }) {
  const fileInputRef = useRef(null);

  const handleUploadClick = (e) => {
    e.preventDefault();
    fileInputRef.current.click();
  };

  const handleFileChange = (e) => {
    if (e.target.files.length > 0) {
      onUpload(e.target.files);
    }
  };

  return (
    <nav className="bg-surface-container-low dark:bg-surface-dim h-screen w-64 fixed left-0 top-0 border-r border-on-surface/5 flex flex-col py-xl px-md z-20">
      <div className="mb-xxl px-sm">
        <div className="flex items-center gap-sm">
          <div className="font-headline-md text-headline-md font-bold text-primary">Clinica AI</div>
        </div>
        <div className="font-label-md text-label-md text-on-surface-variant mt-unit uppercase tracking-widest">Institutional Portal</div>
      </div>
      <div className="flex flex-col gap-sm flex-grow">
        <a href="#" onClick={onClear} className="flex items-center gap-md px-md py-sm rounded-lg hover:bg-primary-container/10 transition-colors duration-200 ease-in-out text-primary dark:text-primary-fixed-dim font-bold border-r-4 border-primary bg-primary-container/5">
          <span className="material-symbols-outlined">dashboard</span>
          <span className="">Clear Chat</span>
        </a>
        <a href="#" onClick={handleUploadClick} className="flex items-center gap-md px-md py-sm rounded-lg hover:bg-primary-container/10 transition-colors duration-200 ease-in-out text-on-surface-variant dark:text-on-surface-variant">
          <span className="material-symbols-outlined">upload_file</span>
          <span className="">Document Upload</span>
        </a>
        <input type="file" ref={fileInputRef} className="hidden" accept=".pdf,.txt" multiple onChange={handleFileChange} />
        <a href="#" onClick={onIngest} className="flex items-center gap-md px-md py-sm rounded-lg hover:bg-primary-container/10 transition-colors duration-200 ease-in-out text-on-surface-variant dark:text-on-surface-variant">
          <span className="material-symbols-outlined">database</span>
          <span className="">Base Dataset</span>
        </a>
      </div>
      <div className="mt-auto border-t border-on-surface/5 pt-lg flex flex-col gap-sm">
        <a className="flex items-center gap-md px-md py-sm rounded-lg hover:bg-primary-container/10 transition-colors duration-200 ease-in-out text-on-surface-variant" href="#">
          <span className="material-symbols-outlined">settings</span>
          <span className="">Settings</span>
        </a>
        <a className="flex items-center gap-md px-md py-sm rounded-lg hover:bg-primary-container/10 transition-colors duration-200 ease-in-out text-on-surface-variant" href="#">
          <span className="material-symbols-outlined">help</span>
          <span className="">Support</span>
        </a>
      </div>
    </nav>
  );
}
