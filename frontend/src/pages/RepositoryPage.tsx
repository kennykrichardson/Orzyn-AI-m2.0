import { Check, Copy, FileText } from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";
import { useState } from "react";
import TypewriterText from "../components/TypewriterText";

export default function RepositoryPage() {

    const location = useLocation();

    const navigate = useNavigate();

    const [copied, setCopied] = useState(false);

    async function copyReport() {

        await navigator.clipboard.writeText(payload?.report ?? "");

        setCopied(true);

        setTimeout(() => {

            setCopied(false);

        }, 2000);

    }

    const payload = location.state as {

        repository: string;

        report: string;

    } | null;

    if (!payload) {

        return (

            <main className="min-h-screen bg-ink text-white">

                <div className="empty-report">

                    <p>No active repository review.</p>

                    <button
                        className="analyze-button max-w-lg"
                        onClick={() => navigate("/")}
                    >
                        New Analysis
                    </button>

                </div>

            </main>

        );

    }

    return (

        <main className="min-h-screen overflow-hidden bg-ink text-white">

            <div className="page-field"/>

            <section className="mx-auto max-w-[1760px] px-6 pt-6 pb-10 md:px-16">

                <article className="report-frame min-h-[74vh]">

                    <header className="report-header">

                        <div className="flex items-center gap-4">

                            <FileText size={26}/>

                            <div>

                                <h1 className="osiris-heading">Engineering Intelligence Report</h1>

                                <p>{payload.repository}</p>

                            </div>

                        </div>

<div className="flex items-center gap-3">

    <button
        className="small-command osiris-button"
        onClick={copyReport}
    >
        {copied ? (
            <>
            <Check size={18} />
                <span>Copied</span>
            </>
        ) : (
            <>
            <Copy size={18} />
                <span>Copy</span>
            </>
        )}
    </button>

    <button
        className="small-command osiris-button"
        onClick={() => navigate("/")}
    >
        New Analysis
    </button>

</div>

                    </header>

                    <div className="report-rule"/>

                    <TypewriterText
                        text={payload.report}
                        speed={3}
                    />

                </article>

            </section>

        </main>

    );

}