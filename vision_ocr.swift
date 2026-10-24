// Apple Vision OCR: vision_ocr <image.png> → JSON array of {text, conf, x, y, w, h} in pixels, top-left origin.
// Build: swiftc -O vision_ocr.swift -o bin/vision_ocr
import Vision
import AppKit

let img = NSImage(contentsOfFile: CommandLine.arguments[1])!
let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil)!
let W = Double(cg.width), H = Double(cg.height)
let req = VNRecognizeTextRequest()
req.recognitionLevel = .accurate
req.usesLanguageCorrection = false  // part numbers, not words
try! VNImageRequestHandler(cgImage: cg).perform([req])
let out: [[String: Any]] = (req.results ?? []).compactMap { o in
    guard let c = o.topCandidates(1).first else { return nil }
    let b = o.boundingBox
    return ["text": c.string, "conf": Double(c.confidence),
            "x": Int(b.minX * W), "y": Int((1 - b.maxY) * H), "w": Int(b.width * W), "h": Int(b.height * H)]
}
FileHandle.standardOutput.write(try! JSONSerialization.data(withJSONObject: out))
