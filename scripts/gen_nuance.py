#!/usr/bin/env python3
"""T3 뉘앙스 문제 (luna 저작) — EP별 의미/뉘앙스 문법. 로직이 원리적으로 못 만드는 유형.

흐름: 프롬프트(EP별) → luna 배치콜(캐시) → 검증(EP01만 형태게이트, 나머진 경량) →
      사람 검토 → 승인(--approve로 needs_review=False). 승인 전엔 서빙 제외.

사용:
  python scripts/gen_nuance.py --ep EP30            # 생성(needs_review=True) → 검토
  python scripts/gen_nuance.py --ep EP30 --approve  # 검토 후 승인(캐시 사용, 토큰 0)
"""
import argparse
import json
import os

import luna

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "data", "nuance")
CACHE_DIR = os.path.join(ROOT, "data", "luna_cache")
N = 15

# EP별 스펙: 문법 설명·제약·검증기. gate="form"은 은/는·이/가 받침 형태검증.
SPECS = {
    "EP01": {
        "qtype": "nuance_particle", "gate": "form",
        "rule": "助詞「은/는」(主題・対比)と「이/가」(主語・新情報)の意味の違い",
        "constraint": ("空所は各問1つだけ。空所直前の単語にパッチムがあれば은/이、なければ는/가。"
                       "正解は必ずこの形態に合わせる。対比する場合はもう一方の助詞は書いておく"
                       "（例: 저( ) 학생이에요. 동생은 회사원이에요.）"),
        "choices_hint": "은/는/이/가",
    },
    "EP30": {
        "qtype": "nuance_go_seo", "gate": "light",
        "rule": "つなぎの語尾「-고」(単純な並列・順序)と「-아/어서」(原因・手段・先行動作)の意味の違い。両方日本語では「〜て」になり混同しやすい",
        "constraint": ("空所は各問1つだけ。動詞・形容詞の語尾部分を空所にする"
                       "（例: 밥을 먹( ) 학교에 가요.）。選択肢は「고」と「아/어서」の該当形を含める"),
        "choices_hint": "고 / 아·어서（例: 먹고 / 먹어서）",
    },
    "EP02": {
        "qtype": "nuance_pronoun", "gate": "light",
        "rule": "人称「저」(丁寧なわたし)と「나」(パンマルのわたし)、「너」(친구へのあなた)の使い分け、および「우리」(所有・所属: 우리 집·우리 학교)",
        "constraint": "空所は各問1つだけ。話す相手が目上か友達かが必ず分かる文脈にする。「당신」は使わない",
        "choices_hint": "저 / 나 / 너 / 우리",
    },
    "EP05": {
        "qtype": "nuance_yesno", "gate": "light",
        "rule": "返事の「네」(はい)「아니요」(いいえ・丁寧)「어」(うん・パンマル)「아니」(ううん・パンマル)と、否定の「아니에요/아니야」(〜ではありません)の違い。返事の「아니요」と否定の「아니에요」の混同が最大の落とし穴",
        "constraint": "空所は各問1つだけ。相手が目上か友達か、返事なのか名詞を否定する文なのかが分かる文脈にする",
        "choices_hint": "네 / 아니요 / 아니에요 / 아니야",
    },
    "EP06": {
        "qtype": "nuance_not_noun", "gate": "light",
        "rule": "名詞の否定「이/가 아니에요」(丁寧)「이/가 아니야」(パンマル)。名詞のパッチム有無で이/가が決まり、相手によって아니에요/아니야が決まる",
        "constraint": ("空所は各問1つだけ。空所の直前の名詞にパッチムがあれば이、なければ가。"
                       "正解は必ずこの形態に合わせる。相手が目上か友達かも文脈で分かるようにする"),
        "choices_hint": "이 아니에요 / 가 아니에요 / 이 아니야 / 가 아니야",
    },
    "EP29": {
        "qtype": "nuance_neomu", "gate": "light",
        "rule": "程度の副詞「너무」(〜すぎる・とても)「아주/정말」(とても)「조금」(少し)の使い分け。너무は本来マイナスの度が過ぎる意味だが、会話では強調にも使う",
        "constraint": "空所は各問1つだけ。度が過ぎて困っているのか、単なる強調なのかが分かる文脈にする",
        "choices_hint": "너무 / 아주 / 정말 / 조금",
    },
    "EP36": {
        "qtype": "nuance_gachi_jeil", "gate": "light",
        "rule": "「같이」(一緒に・〜のように)「제일/가장」(一番)「되다」(〜になる: 名詞+이/가 되다)の使い分け",
        "constraint": "空所は各問1つだけ。되다を問う場合は名詞の後の이/가も正しい形にする",
        "choices_hint": "같이 / 제일 / 이 됐어요 / 가 됐어요",
    },
    "EP37": {
        "qtype": "nuance_beorida", "gate": "light",
        "rule": "「-아/어 버리다」(〜してしまった: 完了＋残念・すっきり)と、副詞「이미」(すでに・既知)「벌써」(もう・予想より早い驚き)の違い",
        "constraint": "空所は各問1つだけ。話し手の気持ち(残念・驚き)が分かる文脈にする",
        "choices_hint": "아·어 버렸어요 / 이미 / 벌써",
    },
    "EP40": {
        "qtype": "nuance_jigeum_bangeum", "gate": "light",
        "rule": "「지금」(今)と「방금」(たった今・直前)の違い、および依存名詞「쪽」(方向)「분」(方・人の敬称)「법」(方法・やり方)の使い分け",
        "constraint": ("空所は各問ちょうど1つ、必ず ( ) の形で書く。_____ など他の空所記号は使わない。"
                       "1問の中で複数の文法項目を混ぜない。次の2グループに分けて作る: "
                       "(a) 時を表す 지금/방금 の対比（방금は直前に終わった動作）。"
                       "(b) 依存名詞 쪽(方向)/분(人の敬称)/법(方法) の選択。"
                       "選択肢は同じグループ内のものだけを並べる"),
        "choices_hint": "지금 / 방금 、または 쪽 / 분 / 법",
    },
    "EP17": {
        "qtype": "nuance_future", "gate": "light",
        "rule": "未来表現「-ㄹ게요」(話し手の意志・約束)「-ㄹ 거예요」(予定・推量)「-ㄹ래요」(希望・意向)の使い分け",
        "constraint": "空所は各問1つだけ。文末の語尾を空所にする（例: 제가 할( ).）。相手や状況が分かる文脈を必ず入れる",
        "choices_hint": "게요 / 거예요 / 래요",
    },
    "EP18": {
        "qtype": "nuance_progressive", "gate": "light",
        "rule": "「-고 있어요」(動作の進行)と「-아/어 있어요」(動作後の状態継続)の違い。日本語ではどちらも「〜ている」",
        "constraint": "空所は各問1つだけ。動詞の後ろを空所にする（例: 문이 열( ).）。自動詞・他動詞の別が分かる文にする",
        "choices_hint": "고 있어요 / 아·어 있어요",
    },
    "EP22": {
        "qtype": "nuance_gunyo", "gate": "light",
        "rule": "感嘆の終結語尾「-구나」(パンマル・独り言)と「-군요」(丁寧)、および動詞は「-는구나/-는군요」・形容詞は「-구나/-군요」という形の違い",
        "constraint": "空所は各問1つだけ。文末を空所にする。相手が目上か友達かが分かる文脈にする",
        "choices_hint": "구나 / 군요 / 는구나 / 는군요",
    },
    "EP23": {
        "qtype": "nuance_ji_ne", "gate": "light",
        "rule": "終結語尾「-지/-죠」(確認・同意を求める、〜でしょ)と「-네/-네요」(今気づいた感想、〜ですね)の違い",
        "constraint": "空所は各問1つだけ。文末を空所にする。既知の確認か、その場での気づきかが分かる文脈にする",
        "choices_hint": "지 / 죠 / 네 / 네요",
    },
    "EP25": {
        "qtype": "nuance_want", "gate": "light",
        "rule": "「-고 싶다」(〜したい)「-기 싫다」(〜したくない)、および三人称の「-고 싶어하다」の使い分け",
        "constraint": "空所は各問1つだけ。主語が誰か（私か第三者か）が分かる文にする",
        "choices_hint": "고 싶어요 / 기 싫어요 / 고 싶어해요",
    },
    "EP27": {
        "qtype": "nuance_ability", "gate": "light",
        "rule": "可能表現「-ㄹ/을 수 있다」の形（パッチム有無で을/ㄹ）と、否定「못」の正しい位置",
        "constraint": ("空所は各問1つだけ。못と-ㄹ 수 없다は多くの文で言い換え可能なので、"
                       "両方を選択肢に入れて正解を1つに絞る問題は絶対に作らないこと。"
                       "代わりに次の2種類だけを作る: (a) -ㄹ 수 있다/없다 の形(語幹のパッチム有無で 을 수/ㄹ 수)を問う。"
                       "(b) 못の位置を問う: 一般動詞は「못 + 動詞」(못 가요)、하다動詞は名詞と하다の間(공부 못 해요)。"
                       "誤答選択肢は形が誤ったものにする（例: 공부 못 해요 ↔ 못 공부해요）"),
        "choices_hint": "을 수 있어요 / ㄹ 수 있어요 / 못 + 動詞 / 名詞 못 해요",
    },
    "EP31": {
        "qtype": "nuance_reason", "gate": "light",
        "rule": "理由の「-아/어서」と「-(으)니까」の違い。命令・勧誘の文には-(으)니까のみ、感謝・謝罪の定型は-아/어서",
        "constraint": "空所は各問1つだけ。後半が命令・勧誘か、単なる叙述かが分かる文にする",
        "choices_hint": "아·어서 / (으)니까",
    },
    "EP32": {
        "qtype": "nuance_ja_janha", "gate": "light",
        "rule": "「-자」(パンマルの勧誘)「-죠」(丁寧な勧誘・確認)「-잖아(요)」(相手も知っている前提の指摘)の使い分け",
        "constraint": "空所は各問1つだけ。文末を空所にする。相手との関係・既知情報かが分かる文脈にする",
        "choices_hint": "자 / 죠 / 잖아요",
    },
    "EP33": {
        "qtype": "nuance_neg_question", "gate": "light",
        "rule": "確認の否定疑問「-는 거 아니야?」(動詞)と「-ㄴ/은 거 아니에요?」(形容詞・過去)の形と意味",
        "constraint": "空所は各問1つだけ。品詞（動詞か形容詞か）と時制が分かる文にする",
        "choices_hint": "는 거 아니에요 / ㄴ·은 거 아니에요",
    },
    "EP35": {
        "qtype": "nuance_intention", "gate": "light",
        "rule": "「-(으)려고」(〜しようと思って、後ろに動作が続く)と「-(으)려고요」(文末で意図を述べる)の使い分け、および「-(으)러」(移動の目的)との違い",
        "constraint": "空所は各問1つだけ。後ろに移動動詞が来るかどうかが分かる文にする",
        "choices_hint": "(으)려고 / (으)려고요 / (으)러",
    },
    "EP38": {
        "qtype": "nuance_contrast", "gate": "light",
        "rule": "「-ㄴ데/-는데」(前置き・状況説明の逆接)と「-지만」(明確な対比の逆接)の違い、および「-아/어 보다」(試み)",
        "constraint": "空所は各問1つだけ。前置きなのか明確な対立なのかが分かる文脈にする",
        "choices_hint": "ㄴ데·는데 / 지만 / 아·어 봤어요",
    },
    "EP39": {
        "qtype": "nuance_adverb", "gate": "light",
        "rule": "副詞化「-게」(形容詞→副詞、広く使える)と「-이/히」(固定した副詞形: 많이·조용히 など)の使い分け",
        "constraint": "空所は各問1つだけ。定着した副詞形がある語とない語を混ぜる",
        "choices_hint": "게 / 이 / 히",
    },
    "EP41": {
        "qtype": "nuance_experience", "gate": "light",
        "rule": "「-ㄴ/은 적 있다」(経験)「밖에 + 否定」(〜しか〜ない)「-고 나서」(〜し終えてから)の使い分け",
        "constraint": "空所は各問1つだけ。経験・限定・順序のどれを問うかが文脈で分かるようにする",
        "choices_hint": "ㄴ·은 적 있어요 / 밖에 / 고 나서",
    },
    "EP42": {
        "qtype": "nuance_sequence_change", "gate": "light",
        "rule": "「-ㄴ/은 후에」(〜した後で)「-기 전에」(〜する前に)「-게 되다」(〜することになる)「-아/어지다」(〜くなる、変化)の使い分け",
        "constraint": "空所は各問1つだけ。前後関係か状態変化かが分かる文にする",
        "choices_hint": "ㄴ·은 후에 / 기 전에 / 게 됐어요 / 아·어졌어요",
    },
}


def build_prompt(spec):
    return (
        "あなたは日本人初級者向けの韓国語問題オーサーです。\n"
        f"{spec['rule']}を問う初級穴埋め問題を{N}問、JSON配列で作ってください。\n"
        f"【厳守ルール】{spec['constraint']}\n"
        "- 空所に正解を入れた文をそのまま読んで自然か必ず確認する。"
        "空所の直前・直後の文字と正解が重複してはいけない（例: 「먹어 보( )」に「봤어요」→「보봤어요」は誤り）。\n"
        "- 選択肢は互いに排他的に。文脈上どれを入れても自然な問題は作らない。\n"
        "- 初級語彙のみ、短い自然な文。パッチムだけでは解けず、意味・文脈で選ぶ問題にする。\n"
        f"- 選択肢は {spec['choices_hint']} など2〜4個。\n"
        "- 各要素: {\"prompt_ko\"(空所は( )), \"choices\", \"answer\", "
        "\"explanation_ja\"(なぜそれか、日本語と対照して)}。\n"
        "JSON配列のみ出力。"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ep", required=True)
    ap.add_argument("--approve", action="store_true", help="검토 후 승인(needs_review=False)")
    ap.add_argument("--reject", default="", help="승인 시 제외할 번호(1-based, 쉼표)")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    reject = {int(x) for x in args.reject.split(",") if x.strip()}
    spec = SPECS[args.ep]
    cache = os.path.join(CACHE_DIR, f"nuance_{args.ep}.json")
    out = os.path.join(OUT_DIR, f"{args.ep}.json")
    validate = luna.valid_nuance if spec["gate"] == "form" else luna.valid_light

    if args.force and os.path.exists(cache):
        os.remove(cache)
    print(f"[{args.ep}] luna 저작 (캐시 {os.path.basename(cache)})...")
    res = luna.call(build_prompt(spec), cache_path=cache)
    valid = [r for r in res if validate(r)]

    os.makedirs(OUT_DIR, exist_ok=True)
    questions = [{
        "qtype": spec["qtype"], "ep_no": args.ep,
        "prompt": r["prompt_ko"], "answer": r["answer"], "choices": r["choices"],
        "difficulty": 3, "source": "authored", "level": 1,
        "explanation": r["explanation_ja"], "needs_review": not args.approve,
        "vocab_key": {"word": None, "homonym_no": None, "pos": None},
    } for i, r in enumerate(valid, 1) if i not in reject]      # 반려분 제외
    json.dump(questions, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    state = "승인(서빙됨)" if args.approve else "검토 대기(needs_review, 서빙제외)"
    print(f"검증 통과 {len(valid)}/{len(res)} → {os.path.relpath(out, ROOT)} [{state}]")
    if not args.approve:
        for i, r in enumerate(valid, 1):
            print(f"  {i}. {r['prompt_ko']}  →{r['answer']} {r['choices']}")
            print(f"     {r['explanation_ja'][:60]}")


if __name__ == "__main__":
    main()
