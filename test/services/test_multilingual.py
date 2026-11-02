from pathlib import Path
from threading import Barrier
from unittest.mock import patch

from app.models.schema import VideoParams
from app.services import multilingual, task


def test_three_languages_overlap_and_keep_separate_audio_and_captions(tmp_path):
    barrier = Barrier(3)
    seen = []

    def audio(child_id, params, script, **kwargs):
        seen.append((child_id, params.voice_name, script, params.custom_audio_file))
        barrier.wait(timeout=5)  # Serial execution would fail here.
        return str(tmp_path / (child_id + '.mp3')), 4, object()

    def folder(child_id):
        p = tmp_path / child_id
        p.mkdir(exist_ok=True)
        return str(p)

    with patch.object(multilingual.utils, 'task_dir', side_effect=folder), \
         patch.object(task, 'generate_audio', side_effect=audio), \
         patch.object(task, 'generate_subtitle', side_effect=lambda id, *a: id + '.srt'), \
         patch.object(task.sm.state, 'update_task'):
        result = multilingual.produce_languages('parent', VideoParams(
            video_subject='Water', video_language='en-US', custom_audio_file='original.mp3',
            language_scripts={'en': 'Water', 'hi': 'पानी', 'es': 'Agua'}), 'Water', '', 'subtitle')
    assert len(seen) == 3
    assert all(item[3] is None for item in seen)
    assert len({item[1] for item in seen}) == 3
    assert all(item['status'] == 'complete' for item in result['language_results'].values())
    assert len({item['subtitle_path'] for item in result['language_results'].values()}) == 3
    assert Path(result['language_manifest']).is_file()


def test_translation_failure_preserves_other_languages_and_reports_failure(tmp_path):
    def folder(child_id):
        p = tmp_path / child_id
        p.mkdir(exist_ok=True)
        return str(p)

    def translation(script, source, code):
        if code == 'hi':
            raise RuntimeError('fixture translation unavailable')
        return script

    with patch.object(multilingual.utils, 'task_dir', side_effect=folder), \
         patch.object(multilingual, 'translate', side_effect=translation), \
         patch.object(task, 'generate_audio', return_value=('audio.mp3', 4, object())), \
         patch.object(task.sm.state, 'update_task'):
        result = multilingual.produce_languages('parent', VideoParams(video_subject='Water'), 'Water', '', 'audio')
    assert result['state'] == task.const.TASK_STATE_FAILED
    assert result['language_results']['en']['status'] == 'complete'
    assert result['language_results']['es']['status'] == 'complete'
    assert result['language_results']['hi']['status'] == 'failed'


def test_translation_is_single_request_and_original_language_is_reused():
    with patch.object(multilingual.llm, '_request_generation', return_value='Agua') as request:
        assert multilingual.translate('Water', 'en-US', 'en') == 'Water'
        request.assert_not_called()
        assert multilingual.translate('Water', 'en-US', 'es') == 'Agua'
        assert request.call_count == 1


def test_video_languages_share_materials_and_render_without_resynthesizing(tmp_path):
    def folder(child_id):
        p = tmp_path / child_id
        p.mkdir(exist_ok=True)
        return str(p)

    with patch.object(multilingual.utils, 'task_dir', side_effect=folder), \
         patch.object(task, 'generate_audio', return_value=('audio.mp3', 4, object())) as speech, \
         patch.object(task, 'generate_subtitle', return_value='subtitle.srt'), \
         patch.object(task, 'get_video_materials', return_value=['shared.mp4']) as materials, \
         patch.object(task, 'generate_final_videos', return_value=(['final.mp4'], [], [])) as render, \
         patch.object(multilingual, 'burn_hindi_subtitles'), \
         patch.object(multilingual.os, 'replace'), \
         patch.object(task.sm.state, 'update_task'):
        result = multilingual.produce_languages('parent', VideoParams(video_subject='Water',
            language_scripts={'en': 'Water', 'hi': 'पानी', 'es': 'Agua'}), 'Water', '', 'video')
    assert speech.call_count == 3
    assert materials.call_count == 1
    assert render.call_count == 3
    assert all(call.args[2] == ['shared.mp4'] for call in render.call_args_list)
    assert len(result['videos']) == 3


def test_audio_request_can_use_multilingual_dispatch(tmp_path):
    from app.models.schema import AudioRequest
    def folder(child_id):
        p = tmp_path / child_id
        p.mkdir(exist_ok=True)
        return str(p)
    with patch.object(multilingual.utils, 'task_dir', side_effect=folder), \
         patch.object(task, 'generate_audio', return_value=('audio.mp3', 4, object())), \
         patch.object(task.sm.state, 'update_task'):
        result = multilingual.produce_languages('parent', AudioRequest(video_script='Water',
            multilingual_enabled=True, language_scripts={'en': 'Water', 'hi': 'पानी', 'es': 'Agua'}),
            'Water', '', 'audio')
    assert result['state'] == task.const.TASK_STATE_COMPLETE
