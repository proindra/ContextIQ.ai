import { gsap } from "gsap";

const CHARACTER_POOL = "abcdefghijklmnopqrstuvwxyz0123456789#%&*+?";
const activeScrambles = new WeakMap<HTMLElement, gsap.core.Tween>();

function randomCharacter(): string {
  return CHARACTER_POOL[Math.floor(Math.random() * CHARACTER_POOL.length)] ?? "?";
}

function scramble(
  element: HTMLElement,
  duration = 0.8,
  delay = 0,
): gsap.core.Tween {
  activeScrambles.get(element)?.kill();
  const finalCharacter = element.dataset.final ?? "";
  const progress = { value: 0 };
  let lastFrame = -1;

  const tween = gsap.to(progress, {
    value: 1,
    duration,
    delay,
    ease: "none",
    onUpdate: () => {
      const frame = Math.floor(progress.value * 14);
      if (frame === lastFrame) return;
      lastFrame = frame;
      element.textContent =
        progress.value >= 1 ? finalCharacter : randomCharacter();
    },
    onComplete: () => {
      element.textContent = finalCharacter;
      activeScrambles.delete(element);
    },
  });
  activeScrambles.set(element, tween);
  return tween;
}

export function initializeHeroMotion(
  hero: HTMLElement | null,
  replayButton?: HTMLButtonElement | null,
): void {
  if (!hero) return;

  const characters = Array.from(
    hero.querySelectorAll<HTMLElement>(".ch[data-final]"),
  );
  const reducedMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)",
  ).matches;

  if (reducedMotion) {
    characters.forEach((character) => {
      character.textContent = character.dataset.final ?? "";
    });
    if (replayButton) replayButton.hidden = true;
    return;
  }

  const context = gsap.context(() => {
    let intro: gsap.core.Timeline | undefined;
    let loops: gsap.core.Tween[] = [];
    let scrambleTimer: gsap.core.Tween | undefined;

    const stopLoops = () => {
      loops.forEach((loop) => loop.kill());
      loops = [];
      scrambleTimer?.kill();
      scrambleTimer = undefined;
    };

    const startLoops = () => {
      stopLoops();
      loops.push(
        gsap.to("#pinG", {
          rotation: 360,
          duration: 6,
          ease: "none",
          repeat: -1,
          transformOrigin: "50% 50%",
        }),
        gsap.to("#astG", {
          rotation: 360,
          duration: 8,
          ease: "none",
          repeat: -1,
          transformOrigin: "50% 50%",
        }),
        gsap.to("#boltP", {
          opacity: 0.35,
          duration: 0.08,
          repeat: -1,
          repeatDelay: 1.8,
          yoyo: true,
        }),
      );

      const scrambleAnotherCharacter = () => {
        const character =
          characters[Math.floor(Math.random() * characters.length)];
        if (character) scramble(character, 0.5);
        scrambleTimer = gsap.delayedCall(
          gsap.utils.random(1.6, 3.2),
          scrambleAnotherCharacter,
        );
      };

      scrambleTimer = gsap.delayedCall(2.6, scrambleAnotherCharacter);
    };

    const playIntro = () => {
      intro?.kill();
      stopLoops();
      gsap.killTweensOf(characters);
      characters.forEach((character) => {
        activeScrambles.get(character)?.kill();
        activeScrambles.delete(character);
      });
      characters.forEach((character) => {
        character.textContent = "\u00a0";
      });

      gsap.set(["#pin", ".ico"], {
        scale: 0,
        transformOrigin: "50% 50%",
      });
      gsap.set("#tag", { opacity: 0, y: 18 });

      intro = gsap.timeline();
      characters.forEach((character, index) => {
        intro?.add(scramble(character, 0.78), index * 0.045);
      });
      intro
        .to("#pin", { scale: 1, rotation: 360, duration: 1, ease: "back.out(2)" }, 0.1)
        .to("#ast", { scale: 1, duration: 0.8, ease: "elastic.out(1, 0.5)" }, 0.3)
        .to("#bolt", { scale: 1, duration: 0.8, ease: "elastic.out(1, 0.5)" }, 0.7)
        .to(
          "#tag",
          { opacity: 1, y: 0, duration: 0.6, stagger: 0.12, ease: "power3.out" },
          1.1,
        )
        .call(startLoops, [], 1.4);
    };

    characters.forEach((character) => {
      character.addEventListener("mouseenter", () => {
        gsap.fromTo(
          character,
          { y: 0 },
          {
            y: "-0.12em",
            rotation: gsap.utils.random(-8, 8),
            duration: 0.18,
            yoyo: true,
            repeat: 1,
            ease: "power2.out",
            overwrite: "auto",
          },
        );
        scramble(character, 0.35);
      });
    });

    replayButton?.addEventListener("click", playIntro);
    playIntro();
  }, hero);

  window.addEventListener("pagehide", () => context.revert(), { once: true });
}
