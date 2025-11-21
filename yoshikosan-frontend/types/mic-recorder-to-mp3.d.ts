declare module 'mic-recorder-to-mp3' {
  interface MicRecorderResult extends Promise<any> {
    getMp3(): Promise<[ArrayBuffer[], Blob]>;
  }

  export default class MicRecorder {
    constructor(options?: { bitRate?: number; encoder?: string });
    start(): Promise<void>;
    stop(): MicRecorderResult;
  }
}
