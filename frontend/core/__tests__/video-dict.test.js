import { describe, it, expect } from 'vitest';

import { applyVideoDictOverrides } from '../components/ArticleForm';


function makeMockEditor() {
  return {
    dictionary: {
      slash_menu: {
        video: {
          title: 'Video',
          subtext: 'Resizable video with caption',
          aliases: ['video', 'videoUpload', 'upload', 'mp4', 'film', 'media', 'url'],
          group: 'Media',
        },
      },
      file_panel: {
        embed: {
          title: 'Embed',
          url_placeholder: 'Enter URL',
          embed_button: {
            image: 'Embed image',
            video: 'Embed video',
            audio: 'Embed audio',
            file: 'Embed file',
          },
        },
      },
    },
  };
}


describe('applyVideoDictOverrides', function () {
  it('renames slash menu title to YouTube', function () {
    var editor = makeMockEditor();
    applyVideoDictOverrides(editor);
    expect(editor.dictionary.slash_menu.video.title).toBe('YouTube');
  });

  it('sets slash menu subtext', function () {
    var editor = makeMockEditor();
    applyVideoDictOverrides(editor);
    expect(editor.dictionary.slash_menu.video.subtext).toBe('Paste a YouTube video URL');
  });

  it('adds youtube and yt aliases', function () {
    var editor = makeMockEditor();
    applyVideoDictOverrides(editor);
    expect(editor.dictionary.slash_menu.video.aliases).toContain('youtube');
    expect(editor.dictionary.slash_menu.video.aliases).toContain('yt');
  });

  it('renames file panel embed tab title', function () {
    var editor = makeMockEditor();
    applyVideoDictOverrides(editor);
    expect(editor.dictionary.file_panel.embed.title).toBe('YouTube URL');
  });

  it('updates embed button text for video', function () {
    var editor = makeMockEditor();
    applyVideoDictOverrides(editor);
    expect(editor.dictionary.file_panel.embed.embed_button.video).toBe('Embed YouTube video');
  });

  it('updates embed placeholder', function () {
    var editor = makeMockEditor();
    applyVideoDictOverrides(editor);
    expect(editor.dictionary.file_panel.embed.url_placeholder).toBe('Paste YouTube video link');
  });
});
