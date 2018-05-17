//
//  testBits.mm
//  bgtfsLib
//
//  Created by Anton Dubrau on 12/13/2013.
//  Copyright (c) 2013 Transit. All rights reserved.
//

#import <XCTest/XCTest.h>
#include "bits.h"
#include <string>
#include <iostream>
#include <fstream>

using namespace namedstruct;
using namespace std;
//TODO - test skip bits

@interface testBits : XCTestCase

@end

@implementation testBits

// return point to buffer filled with data. After this, it's yours, so clean up after yourrself.
static void* getBlob(){
    const int N = 10000;
    uint8_t* blob = (uint8_t*)malloc(N*sizeof(uint8_t));
    for (int i = 0; i < N; ++i){
        blob[i] = i;
    }
    return blob;
}


#pragma mark bits tests
- (void)testBits00 { //simplest direct read test
    void* blob = getBlob();
    XCTAssertEqual(int(readBits(blob,8,16)),0x0201);
    free(blob);
}

- (void)testBits01 {
    void* blob = getBlob();
    XCTAssertEqual(int(readBits(blob,24,16)),0x403);
    free(blob);
}

- (void)testBits02 {
    void* blob = getBlob();
    XCTAssertEqual(int(readBits(blob,24,31)),0x6050403);
    free(blob);
}

- (void)testBits03 { //test sequential reading of single bits
    void* blob = getBlob();
    for (int bitOffset = 0; bitOffset < 400; bitOffset += 13){
        const void* pData = blob;
        uint32_t currentWord;
        int currentBitsLeftInWord;
        startReadBits(pData, bitOffset, currentWord, currentBitsLeftInWord);
        for (int i = 0; i < 50; i++){
            int directlyReadBit = readBits(blob,bitOffset+i,1);
            int sequentialReadBit = readNextBit(pData,currentWord,currentBitsLeftInWord);
            XCTAssertEqual(directlyReadBit,sequentialReadBit);
        }
    }
    free(blob);
}

- (void)testBits04 { //test sequential reading of arbitrary width bit values
    void* blob = getBlob();
    for (int bitOffset = 0; bitOffset < 1000; bitOffset += 13){
        const void* pData = blob;
        uint32_t currentWord;
        int currentBitsLeftInWord;
        startReadBits(pData, bitOffset, currentWord, currentBitsLeftInWord);
        int currentBitOffset = bitOffset;
        for (int i = 0; i < 200; i++){
            int numBits = i & 0x1F; //we can read at most 31 bits
            int directlyReadBits = readBits(blob,currentBitOffset,numBits);
            int sequentialReadBits = readNextBits(pData,currentWord,currentBitsLeftInWord,numBits);
            XCTAssertEqual(directlyReadBits,sequentialReadBits);
            currentBitOffset += numBits;
        }
    }
    free(blob);
}

- (void)testBits05 { //test reverse sequential reading of single bits
    void* blob = getBlob();
    for (int bitOffset = 333; bitOffset < 1000; bitOffset += 13){
        const void* pData = blob;
        uint32_t currentWord;
        int currentBitsLeftInWord;
        startReversedReadBits(pData, bitOffset, currentWord, currentBitsLeftInWord);
        for (int i = 0; i < 300; i++){
            int directlyReadBit = readBits(blob,bitOffset-(i+1),1);
            int sequentialReadBit = readPreviousBit(pData,currentWord,currentBitsLeftInWord);
            XCTAssertEqual(directlyReadBit,sequentialReadBit);
        }
    }
    free(blob);
}

- (void)testBits06 { //test reverse sequential reading of arbitrary width bit values
    void* blob = getBlob();
    for (int bitOffset = 1024*4; bitOffset < 1024*4+1000; bitOffset += 13){
        const void* pData = blob;
        uint32_t currentWord;
        int currentBitsLeftInWord;
        startReversedReadBits(pData, bitOffset, currentWord, currentBitsLeftInWord);
        int currentBitOffset = bitOffset;
        for (int i = 0; i < 32; i++){
            int numBits = i; //we can read at most 31 bits
            currentBitOffset -= numBits;
            if (currentBitsLeftInWord > 0) {
                int directlyReadBits = readBits(blob, currentBitOffset, numBits);
                int sequentialReadBits = readPreviousBits(pData, currentWord, currentBitsLeftInWord, numBits);
                XCTAssertEqual(directlyReadBits, sequentialReadBits);
            }
        }
    }
    free(blob);
}

- (void)testBits08 { //test sequential reading using BitReader
    void* blob = getBlob();
    for (int bitOffset = 0; bitOffset < 1000; bitOffset += 13){
        const void* pData = blob;
        BitReader bits = BitReader(pData, bitOffset);
        int currentBitOffset = bitOffset;
        
        for (int i = 0; i < 200; i++){
            int numBits = i & 0x1F; //we can read at most 31 bits
            int directlyReadBits = readBits(blob,currentBitOffset,numBits);
            int sequentialReadBits = bits.readNextBits(numBits);
            XCTAssertEqual(directlyReadBits,sequentialReadBits);
            currentBitOffset += numBits;
        }
    }
    free(blob);
}

- (void)testBits09 { //test sequential reading of single bits via BitReader
    void* blob = getBlob();
    for (int bitOffset = 0; bitOffset < 400; bitOffset += 13){
        const void* pData = blob;
        BitReader bits = BitReader(pData, bitOffset);
        for (int i = 0; i < 50; i++){
            int directlyReadBit = readBits(blob,bitOffset+i,1);
            int sequentialReadBit = bits.readNextBit();
            XCTAssertEqual(directlyReadBit,sequentialReadBit);
        }
    }
    free(blob);
}


- (void)testBits10Skip { //test skip
    void* blob = getBlob();
    int readBits = 30;
    for (int bitOffset = 0; bitOffset < 1000; bitOffset += 13){
        const void* pData = blob;
        for (int skip = 1; skip < 200; skip++){
            BitReader reader1 = BitReader(pData, bitOffset);
            BitReader reader2 = BitReader(pData, bitOffset);
            // first read some bits
            XCTAssertEqual(reader1.readNextBits(readBits),reader2.readNextBits(readBits));
            // skip
            reader1.skipBits(skip);
            for (int i = 0; i < skip; i++) reader2.readNextBit();
            // compare the bits
            XCTAssertEqual(reader1.readNextBits(readBits),reader2.readNextBits(readBits));
        }
    }
    free(blob);
}

- (void)testRequiredBits {
    /**0 -> 0, 255 -> 8, 256 -> 9 */
    XCTAssertEqual(requiredBits(0),0);
    XCTAssertEqual(requiredBits(255),8);
    XCTAssertEqual(requiredBits(256),9);
}



@end
