"use client";

// Import necessary modules and components
import ThreeCardLayout from "./ThreeCardLayout";
// import NextButton from '@/components/NextButton';
import { ICard } from "@/lib/api";
import { TABLES } from "@/lib/supabase/db";
import { supabase } from "@/lib/supabase/supabaseClient";
import { useEffect, useState } from "react";
import styles from "./feedback.module.scss";
export const dynamic = "force-dynamic";

export default function UserFeedback() {
  // const [currentIndex, setCurrentIndex] = useState<number>(randint(0,177));
  const [userName, setUserName] = useState("");
  const [answered, setAnswered] = useState<Set<number>>(new Set());
  const [fullData, setFullData] = useState<Array<Array<ICard>> | null>(null);
  const [cards, setCards] = useState<ICard[]>([]);

  const [cardArray, setCardArray] = useState<Array<Array<ICard>> | null>(null);

  // Not the best way to do it-- we really should make each of these a new page and the next/prev buttons
  // should be linked to the next/prev page. But this is a quick fix for now.
  // const question_idArray = Array.from({ length: 291 }, (_, index) => index);

  // const handlePrevClick = () => {
  //   if (fullData) {
  //     setCardArray(fullData);
  //     //wraps around
  //     setCurrentIndex(
  //       (currentIndex - 1 + question_idArray.length) % question_idArray.length
  //     );
  //   } else {
  //     alert("Please wait for the rest of the cards to finish loading...");
  //   }
  // };

  const randQuestionId = () => {
    return Math.floor(Math.random() * 237);
  };

  // const shuffleArray = (array: Number[]) => {
  //   for (let i = array.length - 1; i > 0; i--) {
  //     const j = Math.floor(Math.random() * (i + 1));
  //     [array[i], array[j]] = [array[j], array[i]];
  //   }
  //   return array;
  // };

  // const shuffledQuestionIds = shuffleArray(question_idArray);
  const [currentIndex, setCurrentIndex] = useState<number>(0);
  // console.log(`index ${currentIndex}, val ${shuffledQuestionIds[0]}`);
  const handleNextClick = () => {
    // if (fullData) {
    setCardArray(fullData);
    //wraps around
    setCurrentIndex(currentIndex + 1);
    setAnswered(new Set());
    // } else {
    //   alert("Please wait for the rest of the cards to finish loading...");
    // }
  };

  //const handleNameChange = (e) => {
  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setUserName(e.target.value);
  };

  useEffect(() => {
    const getCard = async () => {
      const randId = randQuestionId();
      // console.log("Fetching cards " + randId);
      try {
        const cardsArray: Array<Array<ICard>> = [];
        const { data: newCards, error } = await supabase
          .from(TABLES.FEEDBACK_CARDS)
          .select("*")
          .eq("question_id", randId)
          .eq("model_version", process.env.NEXT_PUBLIC_FEEDBACK_VERSION);
        if (newCards) {
          setCards(newCards);
        }
        setCardArray(cardsArray);
        console.log(cards);
      } catch (error) {
        console.error("Error fetching cards: ", error);
        // Handle the error appropriately in your UI
      }
      // getCards();
    };
    getCard();
  }, [currentIndex]); // Run this effect only once when the component mounts

  // const getCards = async () => {
  //   const cardsArray: Array<Array<ICard>> = [];
  //   try {
  //     for (let i = 1; i < question_idArray.length; i++) {
  //       const { data: cards, error } = await supabase
  //         .from(TABLES.FEEDBACK_CARDS)
  //         .select("*")
  //         .eq("question_id", shuffledQuestionIds[i]);

  //       if (error) {
  //         console.error("Error fetching cards: ", error);
  //         // Handle the error appropriately in your UI
  //       }
  //       // console.log(cards);

  //       if (cards) {
  //         cardsArray.push(cards);
  //       }
  //     }
  //     setFullData(cardsArray);
  //     // console.log(fullData);
  //     //setCurrentIndex(Math.floor(Math.random() * cardsArray.length));
  //   } catch (error) {
  //     console.error("Error fetching cards: ", error);
  //     // Handle the error appropriately in your UI
  //   }
  // };

  if (!cardArray) {
    return <div>Loading...</div>;
  }

  return (
    <div className={styles["feedback-content"]}>
      <div className="h-full px-6 text-primary md:flex">
        <div className="md:grow"></div>
        <div className="pb-24 md:w-3/4 md:max-w-2xl">
          <div className="rounded-lg  p-6 text-primary">
            <label className="mb-2 block text-lg font-bold text-amber-700">
              Please Enter Your Name:
            </label>
            <div className="flex">
              <input
                className="focus:border-blue-500 w-80 appearance-none rounded px-3 py-2 text-lg leading-tight focus:outline-none"
                type="text"
                value={userName}
                onChange={handleNameChange}
                placeholder="Your Name Here"
              />
            </div>
          </div>
          <ThreeCardLayout
            cards={cards}
            userName={userName}
            answered={answered}
            setAnswered={setAnswered}
          />
          {answered.size === 3 && (
            <div className={styles["feedback-submit-button"]}>
              <button
                onClick={handleNextClick}
                className="w-full rounded-lg p-2 text-2xl text-blue md:w-1/2"
              >
                Next question
              </button>
            </div>
          )}

          <p className="mt-6 text-right text-xs">
            {process.env.NEXT_PUBLIC_FEEDBACK_VERSION}
          </p>
        </div>
        <div className="md:grow"></div>
      </div>
    </div>
  );
}
