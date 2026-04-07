from app.services.chunk_service import ChunkService
from app.services.transcript_parser import parse_transcript


def test_parse_json_transcript():
    payload = '{"title":"产品评审会","meeting_date":"2026-04-04 15:00:00","participants":["产品经理A"],"utterances":[{"speaker":"产品经理A","start_time":"00:00:03","end_time":"00:00:18","text":"今天先讨论推荐功能是否上线。"}]}'.encode('utf-8')
    parsed = parse_transcript('meeting.json', payload)
    assert parsed.title == '产品评审会'
    assert parsed.meeting_date is not None
    assert parsed.utterances[0].speaker == '产品经理A'


def test_parse_text_transcript_and_chunk_keywords():
    payload = '[产品经理A] 需要研发本周输出风险评估。\n[研发B] 我负责跟进支付链路稳定性。'.encode('utf-8')
    parsed = parse_transcript('meeting.txt', payload)
    chunks = ChunkService().build_from_utterances(parsed.utterances, 'current_transcript')
    assert len(parsed.utterances) == 2
    assert len(chunks) == 1
    assert any(any(term in keyword for term in ['研发', '支付链路', '风险评估', '稳定性']) for keyword in chunks[0].keywords)


def test_parse_context_speaker_json_transcript():
    payload = (
        '{"id":"0","av_num":123,"context":[["主持人开场。","欢迎各位来到圆桌。"],["大家好，我是项目方代表。"]],'
        '"speaker":[1,2]}'
    ).encode('utf-8')
    parsed = parse_transcript('legacy.json', payload, title_override='量变到质变')
    assert parsed.title == '量变到质变'
    assert len(parsed.utterances) == 3
    assert parsed.utterances[0].speaker == 'Speaker_1'
    assert parsed.utterances[1].speaker == 'Speaker_1'
    assert parsed.utterances[2].speaker == 'Speaker_2'
    assert parsed.utterances[2].text == '大家好，我是项目方代表。'
