import React from 'react';
import { ShieldCheck, Users, Award, Code, Compass, Sparkles, BookOpen } from 'lucide-react';

/**
 * AboutView component
 * Implements Section 4.5 of Planet X UI Documentation:
 * Team information, project mission, core principles, acknowledgements, and disclaimers.
 */
export default function AboutView() {
  const principles = [
    {
      num: '1',
      title: 'Clarity before spectacle',
      desc: 'Users should understand the object, its movement, and the data timestamp quickly without visual distractions.'
    },
    {
      num: '2',
      title: 'Evidence over hype',
      desc: 'Strictly distinguish observed data, calculated estimates, predictions, and illustrative demo content.'
    },
    {
      num: '3',
      title: 'Explore progressively',
      desc: 'Show a clear, accessible summary first; expose deep technical metadata and raw FITS data when requested.'
    },
    {
      num: '4',
      title: 'Trust through provenance',
      desc: 'Display exact data sources, observation timestamps, pipeline versions, and known scientific limitations.'
    },
    {
      num: '5',
      title: 'Accessible by default',
      desc: 'WCAG AA readable contrast, full keyboard navigation support, clear semantic labels, and mobile responsiveness.'
    }
  ];

  return (
    <div className="about-view-container">
      {/* Hero / Mission Card */}
      <section className="card mb-4">
        <div className="about-hero-content">
          <div className="badge badge-surface mb-2">NASA Space Apps Challenge 2026 Project</div>
          <h1 className="section-title">Planet X: Moving Object Finder</h1>
          <p className="hero-tagline text-cyan font-semibold">
            "Find what moved. Understand what you are seeing."
          </p>
          <p className="section-subtitle max-w-3xl mt-2">
            Planet X helps curious beginners, students, educators, and astronomy enthusiasts explore moving objects in the changing sky through a clear, evidence-backed interface. By translating multi-band NASA SPHEREx infrared observations and deep learning anomaly detection into approachable visual evidence, Planet X makes cutting-edge astrophysics transparent and accessible to everyone.
          </p>
        </div>
      </section>

      {/* Team & Location Card */}
      <section className="card mb-4">
        <div className="card-header-row mb-3">
          <div className="flex items-center">
            <Users size={20} className="text-cyan mr-2" />
            <h2 className="card-title">Project Team & Origin</h2>
          </div>
          <span className="badge badge-surface font-mono">Team VU_VioNux</span>
        </div>

        <div className="team-info-grid">
          <div className="team-meta-box">
            <span className="text-xs text-muted">Team Name</span>
            <span className="text-lg font-bold text-primary">VU_VioNux</span>
          </div>
          <div className="team-meta-box">
            <span className="text-xs text-muted">Location</span>
            <span className="text-lg font-bold text-primary">Rajshahi, Bangladesh</span>
          </div>
          <div className="team-meta-box">
            <span className="text-xs text-muted">Event</span>
            <span className="text-lg font-bold text-primary">NASA Space Apps Challenge</span>
          </div>
          <div className="team-meta-box">
            <span className="text-xs text-muted">Product Type</span>
            <span className="text-lg font-bold text-primary">Web-based Moving Object Discovery</span>
          </div>
        </div>

        <div className="team-description mt-4">
          <p className="text-sm text-secondary">
            Team VU_VioNux designed and built Planet X during the NASA Space Apps Challenge with a commitment to scientific rigor, approachable user experience, and full data provenance. Our mission is to democratize deep-sky exploration by bridging advanced machine learning pipelines with intuitive, accessible scientific tools.
          </p>
        </div>
      </section>

      {/* Core UX Principles (Section 1) */}
      <section className="card mb-4">
        <div className="card-header-row mb-3">
          <div className="flex items-center">
            <Compass size={20} className="text-secondary mr-2" />
            <h2 className="card-title">Primary UX & Scientific Principles</h2>
          </div>
          <span className="badge badge-surface">Design System Guidelines</span>
        </div>

        <div className="principles-grid">
          {principles.map((p) => (
            <div key={p.num} className="principle-card">
              <div className="principle-num">{p.num}</div>
              <h3 className="principle-title">{p.title}</h3>
              <p className="principle-desc">{p.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Target Audiences & Use Cases */}
      <section className="card mb-4">
        <h2 className="card-title mb-2">Designed for Progressive Scientific Exploration</h2>
        <p className="text-sm text-secondary leading-relaxed">
          Planet X serves a multi-tiered astronomical workflow: from curious beginners who need plain-language explanations of infrared sky movements, to astrophysics students and educators requiring 102-channel SED profiles and full data provenance, to research astronomers and evaluators seeking rigorous zero-mock multi-modal AI validation and repeatable verification workflows.
        </p>
      </section>

      {/* Acknowledgements & Open-Source Stack (Section 4.5) */}
      <section className="card mb-4">
        <div className="card-header-row mb-3">
          <div className="flex items-center">
            <Code size={20} className="text-info mr-2" />
            <h2 className="card-title">Acknowledgements & Scientific Stack</h2>
          </div>
        </div>

        <div className="acknowledgements-content text-sm text-secondary space-y-3">
          <p>
            Planet X relies on open datasets provided by the <strong>NASA Science Mission Directorate</strong> and the <strong>NASA Infrared Processing and Analysis Center (IPAC)</strong> at Caltech, along with astrometric catalogues from the <strong>European Space Agency (ESA) Gaia Mission</strong>.
          </p>
          <p>
            Built using open-source tools:
          </p>
          <div className="tech-tags-cloud">
            <span className="badge badge-surface">React 18</span>
            <span className="badge badge-surface">Vite</span>
            <span className="badge badge-surface">Lucide Icons</span>
            <span className="badge badge-surface">Python 3.12</span>
            <span className="badge badge-surface">PyTorch</span>
            <span className="badge badge-surface">Astropy</span>
            <span className="badge badge-surface">NumPy</span>
            <span className="badge badge-surface">Space Grotesk</span>
            <span className="badge badge-surface">Inter</span>
            <span className="badge badge-surface">JetBrains Mono</span>
          </div>
        </div>
      </section>

      {/* Mandatory NASA Space Apps Disclaimer (Section 4.5 & 12) */}
      <section className="card border-info">
        <div className="disclaimer-banner-inner">
          <ShieldCheck size={24} className="text-info mr-3 flex-shrink-0" />
          <div>
            <h3 className="font-semibold text-info text-base">NASA Space Apps Challenge Official Notice</h3>
            <p className="text-sm text-secondary mt-1">
              This application was created by Team VU_VioNux for the NASA Space Apps Challenge hackathon. While it makes use of publicly accessible NASA SPHEREx survey data products and scientific literature, it is an independent educational and research exploration tool. This project is not officially endorsed by, sponsored by, or an official product of NASA, the Jet Propulsion Laboratory, or the California Institute of Technology.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

