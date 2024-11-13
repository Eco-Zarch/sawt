#pip3 install rouge-score
from rouge_score import rouge_scorer

scorer = rouge_scorer.RougeScorer(['rouge1'], use_stemmer=True)


cs1 = open("manual1.txt", "r")
candidate_summary1 = cs1.read()
cs2 = open("manual2.txt", "r")
candidate_summary2 = cs2.read()

w1 = open("whisper1.txt", "r")
ref_w1 = w1.read()
w2 = open("whisper2.txt", "r")
ref_w2 = w2.read()

y1 = open("youtube1.txt", "r")
ref_y1 = y1.read()
y2 = open("youtube2.txt", "r")
ref_y2 = y2.read()


# transcription 1
reference_summaries1 = [ref_w1, ref_y1]

scores1 = {key: [] for key in ['rouge1']}

for ref in reference_summaries1:
        temp_scores1 = scorer.score(ref, candidate_summary1)
        for key in temp_scores1:
                scores1[key].append(temp_scores1[key])

for key in scores1:
    print(f'{key}:\n{scores1[key]}')

# transcription 2
reference_summaries2 = [ref_w2, ref_y2]

scores2 = {key: [] for key in ['rouge1']}

for ref in reference_summaries2:
        temp_scores2 = scorer.score(ref, candidate_summary2)
        for key in temp_scores2:
                scores2[key].append(temp_scores2[key])

for key in scores2:
    print(f'{key}:\n{scores2[key]}')