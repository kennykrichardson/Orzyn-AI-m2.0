import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { ShuffleText } from "./ShuffleText";

type BootIntroProps = {
  onComplete: () => void;
};

export function BootIntro({ onComplete }: BootIntroProps) {
  const [done, setDone] = useState(false);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setDone(true);
      onComplete();
    }, 3200);
    return () => window.clearTimeout(timer);
  }, [onComplete]);

  if (done) return null;

  return (
    <motion.div className="boot" exit={{ opacity: 0 }} aria-label="AI system booting">
      <div className="boot__scan" />
      <motion.div
        className="boot__particle"
        initial={{ scale: 0.2, opacity: 0 }}
        animate={{ scale: [0.2, 1, 18, 12], opacity: [0, 1, 1, 0] }}
        transition={{ duration: 2.65, ease: [0.16, 1, 0.3, 1] }}
      />
      <motion.div
        className="boot__logo"
        initial={{ opacity: 0, filter: "blur(16px)", letterSpacing: "1.8rem" }}
        animate={{
          opacity: [0, 1, 1, 0],
          filter: ["blur(16px)", "blur(0px)", "blur(0px)", "blur(18px)"],
          letterSpacing: ["1.8rem", "0.52rem", "0.52rem", "1.1rem"],
        }}
        transition={{ duration: 2.9, delay: 0.35, ease: "easeInOut" }}
      >
        <ShuffleText text="ORZYN" className="osiris-title"/>
        <strong>
          <ShuffleText text="AI" delay={220} className="osiris-title" />
        </strong>
      </motion.div>
      <motion.div
        className="boot__status"
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: [0, 0.75, 0.9, 0], y: [18, 0, 0, -12] }}
        transition={{ duration: 2.8, delay: 0.45 }}
      >
        <ShuffleText text="Reconstructing Interface" delay={420} />
      </motion.div>
      <div className="boot__noise" />
    </motion.div>
  );
}
