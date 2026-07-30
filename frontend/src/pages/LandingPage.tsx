import { ShieldCheck, Sparkles } from "lucide-react";
import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import LoadingStatus from "../components/LoadingStatus";
import RepositoryInput from "../components/RepositoryInput";
import { analyzeRepository, analyzeCode, analyzeDeepCode, extractReportText, ReviewType } from "../services/api";
import { BootIntro } from "../components/BootIntro";
import { ParticleField } from "../components/ParticleField";

export default function LandingPage() {
  const [repository, setRepository] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const [bootFinished, setBootFinished] = useState(false);

  async function onSubmit(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();
    const submitter = (
        event.nativeEvent as SubmitEvent
    ).submitter as HTMLButtonElement | null;

    const selectedReview = (
        submitter?.value as ReviewType
    ) ?? "repository";

    if (!repository.trim() || loading) return;

    setLoading(true);
    setError("");

    try {
let result;

switch (selectedReview) {

    case "repository":

        result = await analyzeRepository(

            repository.trim(),

        );

        break;

    case "code":

        result = await analyzeCode(

            repository.trim(),

        );

        break;

    case "deep":

        result = await analyzeDeepCode(

            repository.trim(),

        );

        break;

}

      const report = extractReportText(result);
      navigate("/repository", {
        state: {
          repository: repository.trim(),
          report,
          raw: result,
        },
      });
    } catch (exception) {
      setError(
        exception instanceof Error
          ? exception.message
          : "Unable to analyze repository."
      );
    } finally {
     setLoading(false);
    }
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-ink text-white">
      {!bootFinished && (
          <BootIntro
              onComplete={() => setBootFinished(true)}
          />
      )}   
      <div className="page-field" />
      <ParticleField />
      <div 
          className="relative z-10 p-6 origin-top"
      >  

      <section className="mx-auto max-w-[1600px] px-6 pb-10 md:px-16">
        <div className="hero-frame min-h-[72vh] px-6 py-12 md:px-12 md:py-20">
            <div className="eyebrow absolute top-1 left-1/2 -translate-x-1/2 z-20">
              <Sparkles size={18} />
              <span>AI-POWERED REPOSITORY INTELLIGENCE</span>
            </div>          
          <div className="corner-grid" />
          <div className="mx-auto max-w-6xl text-center">


            <h1 className="mt-7 osiris-title text-[clamp(4rem,12vw,10.5rem)] font-semibold leading-none text-white">
              ORZYN
              <span className="ml-4 inline-flex translate-y-[-0.52em] rounded-lg border border-white/25 px-3 py-2 osiris-title text-[0.16em] font-normal text-white/85">
                AI
              </span>
            </h1>

            <p className="mt-5 osiris-title text-[clamp(1.2rem,2vw,2rem)] tracking-[0.22em] text-white/68">
              ANALYZE. UNDERSTAND. IMPROVE.
            </p>

            <p className="mx-auto font-mono mt-5 max-w-2xl text-lg leading-8 text-white/56">
              Orzyn AI analyzes your GitHub repository and delivers an engineering report you can trust.
            </p>

            <RepositoryInput
              repository={repository}
              setRepository={setRepository}
              disabled={loading}
              onSubmit={onSubmit}
            />

            {loading && <LoadingStatus />}
            {error && <p className="mx-auto mt-6 max-w-3xl font-mono text-sm text-red-200/80">{error}</p>}

            <div className="mt-7 flex items-center justify-center gap-3 text-white/55">
              <ShieldCheck size={22} />
              <span className="text-lg font-mono">Private by design. Your code stays yours.</span>
            </div>
            <div className="mt-10 border-t border-white/10" />

<footer className="pt-6 pb-2 text-center font-mono text-sm tracking-[0.55em] text-white/36">

    ENGINEERED WITH

    <span className="mx-5 text-lg tracking-normal">
        ⚡
    </span>

    BY

    <a
        href="https://github.com/kennykrichardson"
        target="_blank"
        rel="noopener noreferrer"
        className="ml-3 font-mono font-medium tracking-[0.18em] text-[#C1121F] transition-colors duration-300 hover:text-[#ff4455]"
    >
        KENNY RICHARDSON
    </a>

</footer>
          </div>
        </div>
      </section>
      </div>
    </main>
  );
}
