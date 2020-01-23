//
//  namedStructTests.mm
//  bgtfsLib
//
//  Created by Anton Dubrau on 12/5/2013.
//  Copyright (c) 2013 Transit. All rights reserved.
//

#import <XCTest/XCTest.h>
#include <string>
#include <fstream>
#include <sstream>
#include "stdint.h"
#include "namedStructTests.h"
#include "XCTestCpp.h"
#include <namedstruct/bits.h>
#include <vector>
#include <iostream>

using namespace std;
using namespace namedStructTest;
using namespace namedstruct;

unsigned char* memblockFromPath(const string &path, ifstream::pos_type *sizeReturn = nullptr) {
    ifstream file (path, ios::in|ios::binary|ios::ate);
    
    if (file.is_open()) {
        ifstream::pos_type size = file.tellg();
        unsigned char* memblock = new unsigned char [size];
        file.seekg (0, ios::beg);
        file.read((char*)memblock, static_cast<streamsize>(size));
        file.close();
        
        if (sizeReturn != nullptr) {
            *sizeReturn = size;
        }
        
        return memblock;
    }
    
    return nullptr;
}


@interface namedStructTestCase : XCTestCase {
    string genDir;
}

@end

@implementation namedStructTestCase
- (void)setUp {
    [super setUp];
    
   genDir = string([[[[NSBundle bundleForClass:[self class]] resourcePath] stringByAppendingPathComponent:@"localTestFiles"] UTF8String]);
}

- (void)testStruct00 {
    auto aStruct = (testStruct0*)memblockFromPath(genDir+"/testStruct0.bin");
    XCTAssertFalse(aStruct==nullptr);
}

- (void)testStruct01 {
    auto aStruct = (testStruct1*)memblockFromPath(genDir+"/testStruct1.bin");
    XCTAssertFalse(aStruct==nullptr);
    XCTAssertEqual(aStruct->bla,234);
}

- (void)testStruct02 {
    auto aStruct = (testStruct2*)memblockFromPath(genDir+"/testStruct2.bin");
    XCTAssertFalse(aStruct==nullptr);
    XCTAssertEqual((int8_t)59,aStruct->woot);
}

- (void)testStruct03 {
    auto aStruct = (testStruct3*)memblockFromPath(genDir+"/testStruct3.bin");
    XCTAssertFalse(aStruct==nullptr);
    XCTAssertEqual((int8_t)4,aStruct->four);
    XCTAssertNotEqual(0,aStruct->nestedMemberByteOffset);
    auto nestedStruct = aStruct->getNestedMember();
    XCTAssertNotEqual(nestedStruct,nullptr);
    XCTAssertEqual((int8_t)23,nestedStruct->bla);
}

- (void)testStruct04 {
    auto aStruct = (testStruct4*)memblockFromPath(genDir+"/testStruct4.bin");
    XCTAssertFalse(aStruct==nullptr);
    XCTAssertNotEqual(0,aStruct->helloByteOffset);
    char* hello = aStruct->getHello();
    XCTAssertNotEqual(hello,nullptr);
    XCTAssertEqualCpp("hello world!",std::string(hello));
}

- (void)testStruct05 {
    auto aStruct = (testStruct5*)memblockFromPath(genDir+"/testStruct5.bin");
    XCTAssertFalse(aStruct==nullptr);
    XCTAssertNotEqual(0,aStruct->unicodeStringByteOffset);
    char* hello = aStruct->getUnicodeString();
    XCTAssertNotEqual(hello,nullptr);
    string helloTest = "Société de transport de Montréal";
    XCTAssertEqualCpp(helloTest, std::string(hello));
}

- (void)testStruct06 {
    auto aStruct = (testStruct6*)memblockFromPath(genDir+"/testStruct6.bin");
    XCTAssertFalse(aStruct==nullptr);
    XCTAssertNotEqual(0,aStruct->myBlobByteOffset);
    auto bits = aStruct->getMyBlob();
    XCTAssertNotEqual(bits,nullptr);
    XCTAssertEqual(int(*(uint8_t*)bits),0x92,"bits should be [01001001]=0x92");
}

- (void)testStruct07 {
    auto aStruct = (testStruct7*)memblockFromPath(genDir+"/testStruct7.bin");
    XCTAssertFalse(aStruct==nullptr);
    XCTAssertEqual(aStruct->anInt8, int8_t(8));
    XCTAssertEqual(aStruct->anInt32, int32_t(-32));
    XCTAssertEqual(aStruct->anUint32, uint32_t(32));
    XCTAssertNotEqual(0,aStruct->aStringByteOffset);
    char* s = aStruct->getAString();
    XCTAssertEqualCpp("hello world",std::string(s));
    XCTAssertNotEqual(0,aStruct->aBlobByteOffset);
    auto bits = aStruct->getABlob();
    XCTAssertEqual(int(*(uint8_t*)bits),0x46,"bits should be [0110001]=0x46");
}



- (void)testStruct08 {
    auto aStruct = (testStruct8*)memblockFromPath(genDir+"/testStruct8.bin");
    XCTAssertFalse(aStruct==nullptr);
    XCTAssertNotEqual(aStruct->longBlobByteOffset,0);
    void* pBlob = aStruct->getLongBlob();
    XCTAssertNotEqual(pBlob,nullptr);
    int bitOffset = 0;
    for(int i=0;i<32;++i){
        //find how many bits i has, i.e. the MSB
        int numBits = 0, v = i;
        while (v) { numBits++; v >>= 1; }
        XCTAssertEqual((uint32_t)i,readBits(pBlob,bitOffset,numBits));
        bitOffset += numBits;
    }
}

- (void)testStruct09 {
    auto aStruct = (testStruct9*)memblockFromPath(genDir+"/testStruct9.bin");
    XCTAssertFalse(aStruct==nullptr);
    XCTAssertNotEqual(0,aStruct->longStringByteOffset);
    char* chars = aStruct->getLongString();
    XCTAssertNotEqual(chars,nullptr);
    ostringstream stream;
    stream << 0;
    for(int i=1;i<100;++i){
        stream << "-" << i;
    }
    XCTAssertEqualCpp(stream.str(),std::string(chars));
}

- (void)testStruct10 {
    auto aStruct = (testStruct10*)memblockFromPath(genDir+"/testStruct10.bin");
    XCTAssertFalse(aStruct==nullptr);
    XCTAssertEqual(testStruct10::EVERYTHING, 43);
}

- (void)testStruct11 {
    auto aStruct = (testStruct11*)memblockFromPath(genDir+"/testStruct11.bin");
    XCTAssertFalse(aStruct==nullptr);
    XCTAssertEqual(1,aStruct->value);
    XCTAssertNotEqual(0,aStruct->nextByteOffset);
    auto bStruct = aStruct->getNext();
    XCTAssertEqual(2,bStruct->value);
    XCTAssertEqual(0,int(bStruct->nextByteOffset));
}

- (void)testStruct12 {
    auto aStruct = (testStruct12*)memblockFromPath(genDir+"/testStruct12.bin");
    XCTAssertFalse(aStruct==nullptr);
    XCTAssertEqual((int8_t)4,aStruct->aValue);
    XCTAssertNotEqual(0,aStruct->anotherStructByteOffset);
    testNestedStruct1* nestedStruct = aStruct->getAnotherStruct();
    XCTAssertNotEqual(nestedStruct,nullptr);
    XCTAssertEqual((int8_t)123,nestedStruct->anotherValue);
}



- (void)testStruct13 {
    auto aStruct = (testStruct13*)memblockFromPath(genDir+"/testStruct13.bin");
    XCTAssertFalse(aStruct==nullptr);
    XCTAssertEqual(aStruct->x,(int8_t)4);
    XCTAssertEqual((uintptr_t)&(aStruct->immediateStruct) % 4, (uintptr_t)0,"structs should be word aligned");
    XCTAssertEqual(aStruct->immediateStruct.y, -123);
}


- (void)testStruct14 {
    auto aStruct = (testStruct14*)memblockFromPath(genDir+"/testStruct14.bin");
    XCTAssertFalse(aStruct==nullptr);
    XCTAssertEqual(aStruct->number, 23);
    XCTAssertEqualCpp(string(aStruct->getString()),"helluWorld");
    XCTAssertEqual(aStruct->refByteOffset,0);
}

- (void)testStruct15 {
    auto aStruct = (testStruct15*)memblockFromPath(genDir+"/testStruct15.bin");
    XCTAssertFalse(aStruct==nullptr);
    XCTAssertEqualCpp(string(aStruct->immedateString),"something something...");
}

- (void)testStruct16 {
    auto aStruct = (testStruct16*)memblockFromPath(genDir+"/testStruct16.bin");
    XCTAssertFalse(aStruct==nullptr);
    XCTAssertEqualCpp(string(aStruct->fixedString),"yet another");
    XCTAssertEqual((int)offsetof(testStruct16,nonFixedString),30);
    XCTAssertEqualCpp(string(aStruct->nonFixedString),"fooBar");
}

- (void)testStruct17 {
    auto aStruct = (testStruct17*)memblockFromPath(genDir+"/testStruct17.bin");
    XCTAssertFalse(aStruct==nullptr);
    auto sArray = aStruct->getStructArray();
    XCTAssertEqualCpp(string(sArray[0].getName()),"John");
    XCTAssertEqualCpp(string(sArray[1].getName()),"Jane");
    XCTAssertEqualCpp(string(sArray[2].getName()),"Bob");
    XCTAssertEqual(sArray[0].x,(int8_t)7);
    XCTAssertEqual(sArray[1].x,(int8_t)13);
    XCTAssertEqual(sArray[2].x,(int8_t)37);
}

- (void)testStruct18 {
    auto aStruct = (testStruct18*)memblockFromPath(genDir+"/testStruct18.bin");
    XCTAssertFalse(aStruct==nullptr);
    elementStruct1* sArray = aStruct->structArray;
    XCTAssertEqual((uintptr_t)&(sArray[1]) % 4, (uintptr_t)0,"structs should be wod aligned");
    XCTAssertEqual((int)sArray[0].foo,7);
    XCTAssertEqual((int)sArray[1].foo,9);
    XCTAssertEqual(aStruct->x,234);
    
}

- (void)testStruct19 {
    auto aStruct = (testStruct19*)memblockFromPath(genDir+"/testStruct19.bin");
    XCTAssertFalse(aStruct==nullptr);
    elementStruct2* sArray = aStruct->structArray;
    XCTAssertEqualCpp(string(sArray[0].getAname()),"Blob");
    XCTAssertEqualCpp(string(sArray[1].getAname()),"Blubb");
    XCTAssertEqual(aStruct->xyz,34);
}

- (void)testStruct20 {
    auto aStruct = (testStruct20*)memblockFromPath(genDir+"/testStruct20.bin");
    XCTAssertFalse(aStruct==nullptr);
    XCTAssertEqual(aStruct->aChar,'!');
    XCTAssertEqual(aStruct->bChar,'\'');
    XCTAssertEqual(aStruct->cChar,'\"');
    XCTAssertEqual(aStruct->dChar,'\n');
}


- (void)testStruct21 {
    auto aStruct = (testStruct21*)memblockFromPath(genDir+"/testStruct21.bin");
    XCTAssertFalse(aStruct==nullptr);
    XCTAssertEqual(aStruct->a,'!');
    XCTAssertEqual(aStruct->b,'\'');
    XCTAssertEqual(aStruct->c,'\"');
    XCTAssertEqual(aStruct->d,'\n');
    XCTAssertEqual(aStruct->e,'\0');
}

- (void)testStruct22 {
    auto aStruct = (testStruct22*)memblockFromPath(genDir+"/testStruct22.bin");
    XCTAssertFalse(aStruct==nullptr);
    XCTAssertEqual(aStruct->magic[0],'a');
    XCTAssertEqual(aStruct->magic[1],'b');
    XCTAssertEqual(aStruct->magic[2],'c');
    XCTAssertEqual(aStruct->magic[3],'d');
    XCTAssertEqual(*(aStruct->magic+4),'!');
    XCTAssertEqual(aStruct->end,'!');
}


- (void)testStruct23 {
    auto aStruct = (testStruct23*)memblockFromPath(genDir+"/testStruct23.bin");
    XCTAssertFalse(aStruct==nullptr);
    XCTAssertEqual(aStruct->noStringByteOffset,0);
}

- (void)testStruct24 {
    auto aStruct = (testStruct24*)memblockFromPath(genDir+"/testStruct24.bin");
    XCTAssertFalse(aStruct==nullptr);
    XCTAssertEqual(aStruct->structArray[0].maybeStringByteOffset,0);
    XCTAssertEqualCpp(string(aStruct->structArray[1].getMaybeString()),"omg yes!");
}

- (void)testStruct25 {
    auto aStruct = (testStruct25*)memblockFromPath(genDir+"/testStruct25.bin");
    XCTAssertFalse(aStruct==nullptr);
    XCTAssertEqual(static_cast<int>(sizeof(testStruct25)),8);
    XCTAssertEqualCpp(string(aStruct->getA()),"this is a string");
    XCTAssertEqualCpp(string(aStruct->getB()),"this is another string");
    XCTAssertEqualCpp(string(aStruct->getC()),"aaand another");
    XCTAssertEqualCpp(string(aStruct->getD()),"this is the last");
}

- (void)testStruct26 {
    auto aStruct = (testStruct26*)memblockFromPath(genDir+"/testStruct26.bin");
    XCTAssertFalse(aStruct==nullptr);
    auto refArray = aStruct->getRefArray();
    XCTAssertEqualCpp(string(refArray->get(0)),"test");
    XCTAssertEqualCpp(string(refArray->get(1)),"foo");
    XCTAssertEqualCpp(string(refArray->get(2)),"bar");
    
}

- (void)testStruct27 {
    auto aStruct = (testStruct27*)memblockFromPath(genDir+"/testStruct27.bin");
    XCTAssertFalse(aStruct==nullptr);
    auto refArray = aStruct->getBRefArray();
    XCTAssertEqualCpp(refArray->elementByteOffsets[0],0);
    XCTAssertEqualCpp(string(refArray->get(1)),"foo");
    XCTAssertEqualCpp(refArray->elementByteOffsets[2],0);
}

- (void)testStruct28 {
    auto aStruct = (testStruct28*)memblockFromPath(genDir+"/testStruct28.bin");
    XCTAssertFalse(aStruct==nullptr);
    voidRefArray* a = aStruct->getCRefArray();
    XCTAssertEqual(a->elementByteOffsets[0], 0);
}

- (void)testStruct29 {
    auto aStruct = (testStruct29*)memblockFromPath(genDir+"/testStruct29.bin");
    XCTAssertFalse(aStruct==nullptr);
    elementStruct4* s;
    s = aStruct->getRArray()->get(0);
    XCTAssertEqual(s->age, 56);
    XCTAssertEqualCpp(string(s->name),"Vader");
    s = aStruct->getRArray()->get(1);
    XCTAssertEqual(s->age, 22);
    XCTAssertEqualCpp(string(s->name),"Luc");
    s = aStruct->getRArray()->get(2);
    XCTAssertEqual(s->age, 22);
    XCTAssertEqualCpp(string(s->name),"Lea");
    
}

- (void)testStruct30 {
    auto aStruct = (testStruct30*)memblockFromPath(genDir+"/testStruct30.bin");
    XCTAssertFalse(aStruct==nullptr);
    charRef8Array* a = aStruct->getStrings();
    XCTAssertEqualCpp(string(a->get(0)),"Mercury");
    XCTAssertEqualCpp(string(a->get(1)),"Venus");
    XCTAssertEqualCpp(string(a->get(2)),"Earth");
    XCTAssertEqualCpp(string(a->get(3)),"Mars");
    XCTAssertEqualCpp(string(a->get(4)),"Jupiter");
    XCTAssertEqualCpp(string(a->get(5)),"Saturn");
    XCTAssertEqualCpp(string(a->get(6)),"Uranus");
    XCTAssertEqualCpp(string(a->get(7)),"Neptune");
    XCTAssertEqual(a->elementByteOffsets[8],(uint8_t)0);
}

- (void)testStruct31 {
    auto aStruct = (testStruct31*)memblockFromPath(genDir+"/testStruct31.bin");
    XCTAssertFalse(aStruct==nullptr);
    XCTAssertEqual(aStruct->getSizes()[0],3);
    XCTAssertEqual(aStruct->getSizes()[1],2);
    XCTAssertEqual(aStruct->getSizes()[2],4);
    int32_tRef16Array* a = aStruct->getArray();
    XCTAssertEqual(a->get(0)[0],4);
    XCTAssertEqual(a->get(0)[1],5);
    XCTAssertEqual(a->get(0)[2],6);
    XCTAssertEqual(a->get(1)[0],2);
    XCTAssertEqual(a->get(1)[1],3);
    XCTAssertEqual(a->get(2)[0],5);
    XCTAssertEqual(a->get(2)[1],6);
    XCTAssertEqual(a->get(2)[2],7);
    XCTAssertEqual(a->get(2)[3],7);
}

- (void)testStruct32 {
    auto aStruct = (testStruct32*)memblockFromPath(genDir+"/testStruct32.bin");
    XCTAssertFalse(aStruct==nullptr);
    XCTAssertEqual(aStruct->fixedArray.elementByteOffsets[0],0);
    XCTAssertEqualCpp(string(aStruct->fixedArray.get(1)),"foo");
    XCTAssertEqualCpp(string(aStruct->fixedArray.get(2)),"bar");
}



- (void)testStruct33 {
    auto aStruct = (testStruct33*)memblockFromPath(genDir+"/testStruct33.bin");
    XCTAssertFalse(aStruct==nullptr);
    charSize2RefArrayRef16ArrayRefArray* refsrefsrefs = aStruct->getRefsrefsrefs();
    charSize2RefArrayRef16Array* refsrefs;
    charSize2RefArray* refs;
    refsrefs = refsrefsrefs->get(0);
    refs = refsrefs->get(0);
    XCTAssertEqualCpp(string(refs->get(0)),"foo");
    XCTAssertEqualCpp(string(refs->get(1)),"bar");
    refs = refsrefs->get(1);
    XCTAssertEqual(refs->elementByteOffsets[0],0);
    XCTAssertEqual(refs->elementByteOffsets[1],0);
    refs = refsrefs->get(2);
    XCTAssertEqualCpp(string(refs->get(0)),"abcdefghijklmnopqrstuvwxyz");
    refsrefs = refsrefsrefs->get(1);
    refs = refsrefs->get(0);
    XCTAssertEqualCpp(string(refs->get(0)),"2_foo");
    XCTAssertEqualCpp(string(refs->get(1)),"bar_2");
    refs = refsrefs->get(1);
    XCTAssertEqual(refs->elementByteOffsets[0],0);
    XCTAssertEqualCpp(string(refs->get(1)),"some!");
    refs = refsrefs->get(2);
    XCTAssertEqualCpp(string(refs->get(0)),"not again");
    XCTAssertEqual(aStruct->terminal,123456);
}

- (void)testStruct34bitfields0 {
    auto aStruct = (testStruct34*)memblockFromPath(genDir+"/testStruct34.bin");
    XCTAssertFalse(aStruct==nullptr);
    XCTAssertEqual(aStruct->flags.getAFlag(),1);
    XCTAssertEqual(aStruct->flags.getBFlag(),0);
    XCTAssertEqual(aStruct->flags.getCFlag(),1);
    XCTAssertEqual(aStruct->flags.getValues(),3);
    XCTAssertEqual(aStruct->smallInts.getAFlag(),0);
    XCTAssertEqual(aStruct->smallInts.getB(),127);
    XCTAssertEqual(aStruct->smallInts.getC(),0);
    XCTAssertEqual(aStruct->smallInts.getD(),7);
    XCTAssertEqual(aStruct->terminal,567);
    
}

- (void)testStruct35bitfields1 {
    auto aStruct = (testStruct35*)memblockFromPath(genDir+"/testStruct35.bin");
    XCTAssertFalse(aStruct==nullptr);
    timeBitField time;
    time = aStruct->getDates()[0];
    XCTAssertEqual(time.getYear(),  2011);
    XCTAssertEqual(time.getMonth(), 11);
    XCTAssertEqual(time.getDay(),   11);
    XCTAssertEqual(time.getHour(),  9);
    XCTAssertEqual(time.getMinute(),23);
    time = aStruct->getDates()[1];
    XCTAssertEqual(time.getYear(),  2012);
    XCTAssertEqual(time.getMonth(), 12);
    XCTAssertEqual(time.getDay(),   12);
    XCTAssertEqual(time.getHour(),  10);
    XCTAssertEqual(time.getMinute(),24);
}


- (void)testStruct36Alignments {
    auto aStruct = (testStruct36*)memblockFromPath(genDir+"/testStruct36.bin");
    XCTAssertFalse(aStruct==nullptr);
    auto s0 = aStruct->getS0();
    XCTAssertFalse((void*)aStruct==(void*)s0);
    XCTAssertEqual((int)s0->x,171);
    XCTAssertEqual((int)s0->y,171);
    XCTAssertEqualCpp((int)alignof(testNestedStruct3),1);
    
    auto s1 = aStruct->getS1();
    XCTAssertFalse((void*)aStruct==(void*)s1);
    XCTAssertEqual(s1->x,(uint16_t)44204);
    XCTAssertTrue((int)alignof(testNestedStruct4)<=2);
    
    auto s2 = aStruct->getS2();
    XCTAssertFalse((void*)aStruct==(void*)s2);
    XCTAssertEqual(s2->x,(uint32_t)2913840557);
    XCTAssertTrue((int)alignof(testNestedStruct5)<=4);
    
    auto s3 = aStruct->getS3();
    XCTAssertFalse((void*)aStruct==(void*)s3);
    XCTAssertEqual(s3->x,12587190073842184111UL);
    XCTAssertEqual(s3->y,9332165983064197000UL);
    XCTAssertTrue((int)alignof(testNestedStruct6)<=8);
}

- (void)testStruct37Alignments {
    auto aStruct = (testStruct37*)memblockFromPath(genDir+"/testStruct37.bin");
    XCTAssertFalse(aStruct==nullptr);
    XCTAssertEqual((int)aStruct->stringRefByteOffset,0);
    XCTAssertEqual((int)aStruct->bitFieldReferenceByteOffset,0);
    XCTAssertEqual((int)aStruct->int8ArrayRefByteOffset,0);
    XCTAssertEqual((int)aStruct->uint8RefByteOffset,0);
}


- (void)testStruct38values {
    auto aStruct = (testStruct38*)memblockFromPath(genDir+"/testStruct38.bin");
    vector<int> expected = {0,1,1,0,0,1,0,1};
    for (int i = 0; i < expected.size(); i++){
        int read = aStruct->getBitArray()->getBit(i);
        XCTAssertEqual(read, expected[i]);
    }
    XCTAssertEqual(aStruct->getBitArray()->getNumFields(),1);
}

- (void)testStruct38other {
    auto aStruct = (testStruct38*)memblockFromPath(genDir+"/testStruct38.bin");
    auto bitArray = aStruct->getBitArray();
    XCTAssertEqual(bitArray->getBitBitOffset(0),48);
    XCTAssertEqual(bitArray->getBitBitOffset(5),53);
    XCTAssertEqual(bitArray->getBitNumBits(),1);
}


- (void)testStruct39values {
    auto aStruct = (testStruct39*)memblockFromPath(genDir+"/testStruct39.bin");
    vector<vector<uint32_t>> expected = {{0,12},{0,4},{0,0},{0,63}};
    auto bitArray = aStruct->getPairArray();
    for (int i = 0; i < expected.size(); i++){
        //test by field name
        XCTAssertEqual(expected[i][0],bitArray->getA(i));
        XCTAssertEqual(expected[i][1],bitArray->getB(i));
        //test by field index
        XCTAssertEqual(expected[i][0],bitArray->getByFieldIndex(0, i));
        XCTAssertEqual(expected[i][1],bitArray->getByFieldIndex(1, i));
    }
}

- (void)testStruct39other {
    auto aStruct = (testStruct39*)memblockFromPath(genDir+"/testStruct39.bin");
    auto bitArray = aStruct->getPairArray();
    XCTAssertEqual(bitArray->getABitOffset(0),64);
    XCTAssertEqual(bitArray->getABitOffset(5),64+5*6);
    XCTAssertEqual(bitArray->getANumBits(),0);
    XCTAssertEqual(bitArray->getBNumBits(),6);
    XCTAssertEqual(bitArray->getNumFields(),2);

}

- (void)testStruct40values {
    auto aStruct = (testStruct40*)memblockFromPath(genDir+"/testStruct40.bin");
    vector<vector<uint32_t>> expected = {
        {3,4,5},{10,0,3},{36,0,0},{0,0,0},
        {1<<30,0,0},{1<<30,0,0},{1<<30,0,0},{1<<30,0,1},{1<<30,0,2}};
    auto bitArray = &(aStruct->bitArray);
    for (int i = 0; i < expected.size(); i++){
        XCTAssertEqual(expected[i][0],bitArray->getA(i));
        XCTAssertEqual(expected[i][2],bitArray->getFoo(i));
        XCTAssertEqual(expected[i][1],
                       BitReader(bitArray, bitArray->getBBitOffset(i)).readNextBits(30));
    }
}

- (void)testStruct40other {
    auto aStruct = (testStruct40*)memblockFromPath(genDir+"/testStruct40.bin");
    auto bitArray = &(aStruct->bitArray);
    XCTAssertEqual(bitArray->getANumBits(),31);
    XCTAssertEqual(bitArray->getBNumBits(),50);
    XCTAssertEqual(bitArray->getFooNumBits(),3);
    XCTAssertEqual(bitArray->getNumFields(),3);
}

// variable length bitfield array tests:
std::vector<std::vector<int>> test41Data = {
    {1,0,32,23},
    {1,0,17,53},
    {0,0,42,59}
};

#define TEST41VALUES \
for (int elementIndex = 0; elementIndex < 3; elementIndex++) { \
    for (int fieldIndex = 0; fieldIndex < aStruct->bitArray.getNumFields(); fieldIndex++) { \
        XCTAssertEqual(aStruct->bitArray.getByFieldIndex(fieldIndex, elementIndex), test41Data[elementIndex][fieldIndex]); \
    } \
}

- (void)testStruct41ATypeAData {
    auto aStruct = (testStruct41A*)memblockFromPath(genDir+"/testStruct41A.bin");
    XCTAssertEqual(aStruct->bitArray.getNumFields(), 2);
    TEST41VALUES
}

- (void)testStruct41ATypeBData {
    auto aStruct = (testStruct41A*)memblockFromPath(genDir+"/testStruct41B.bin");
    XCTAssertEqual(aStruct->bitArray.getNumFields(), 3);
    TEST41VALUES
}

- (void)testStruct41ATypeCData {
    auto aStruct = (testStruct41A*)memblockFromPath(genDir+"/testStruct41C.bin");
    XCTAssertEqual(aStruct->bitArray.getNumFields(), 4);
    TEST41VALUES
}

- (void)testStruct41BTypeAData {
    auto aStruct = (testStruct41B*)memblockFromPath(genDir+"/testStruct41A.bin");
    XCTAssertEqual(aStruct->bitArray.getNumFields(), 2);
    TEST41VALUES
}

- (void)testStruct41BTypeBData {
    auto aStruct = (testStruct41B*)memblockFromPath(genDir+"/testStruct41B.bin");
    XCTAssertEqual(aStruct->bitArray.getNumFields(), 3);
    TEST41VALUES
}

- (void)testStruct41BTypeCData {
    auto aStruct = (testStruct41B*)memblockFromPath(genDir+"/testStruct41C.bin");
    XCTAssertEqual(aStruct->bitArray.getNumFields(), 4);
    TEST41VALUES
}

- (void)testStruct41CTypeAData {
    auto aStruct = (testStruct41C*)memblockFromPath(genDir+"/testStruct41A.bin");
    XCTAssertEqual(aStruct->bitArray.getNumFields(), 2);
    TEST41VALUES
}

- (void)testStruct41CTypeBData {
    auto aStruct = (testStruct41C*)memblockFromPath(genDir+"/testStruct41B.bin");
    XCTAssertEqual(aStruct->bitArray.getNumFields(), 3);
    TEST41VALUES
}

- (void)testStruct41CTypeCData {
    auto aStruct = (testStruct41C*)memblockFromPath(genDir+"/testStruct41C.bin");
    XCTAssertEqual(aStruct->bitArray.getNumFields(), 4);
    TEST41VALUES
}


- (void)testStruct42 {
    auto aStruct = (testStruct42*)memblockFromPath(genDir+"/testStruct42.bin");
    XCTAssertEqual(aStruct->getGender(), GenderEnum::OTHER);
    XCTAssertEqual(aStruct->getNation(), NationEnum::OTHER);
    XCTAssertEqual(aStruct->getParty(),  PartyEnum::GREEN);
}

- (void)testStruct43 {
    auto aStruct = (testStruct43*)memblockFromPath(genDir+"/testStruct43.bin");
    XCTAssertEqual(aStruct->bitfield.getS1(), 1);
    XCTAssertEqual(aStruct->bitfield.getS2(),-2);
    XCTAssertEqual(aStruct->bitfield.getS3(),-127);
    XCTAssertEqual(aStruct->bitfield.getEmpty(), 0);
}

- (void)testStruct44 {
    auto aStruct = (testStruct44*)memblockFromPath(genDir+"/testStruct44.bin");
    XCTAssertEqual(aStruct->bitfield.getField(), -2147483648);
}

- (void)testStruct45 {
    auto aStruct = (testStruct45*)memblockFromPath(genDir+"/testStruct45.bin");
    XCTAssertEqual(aStruct->bitfield.getGender(), GenderEnum::OTHER);
    XCTAssertEqual(aStruct->bitfield.getParty(),  PartyEnum::GREEN);
    XCTAssertEqual(aStruct->bitfield.getYes(),    YesEnum::yes);
    XCTAssertEqual(aStruct->bitfield.getNo(),     NoEnum::no);
    XCTAssertEqual(aStruct->bitfield.getSignedEmpty(), 0);
    XCTAssertEqual(aStruct->bitfield.getOther(),  1);
    
    aStruct->bitfield.setParty(PartyEnum::CONSERVATIVE);
    XCTAssertEqual(aStruct->bitfield.getGender(), GenderEnum::OTHER);
    XCTAssertEqual(aStruct->bitfield.getParty(),  PartyEnum::CONSERVATIVE);
    XCTAssertEqual(aStruct->bitfield.getNo(),     NoEnum::no);
    
    aStruct->bitfield.setGender(GenderEnum::FEMALE);
    XCTAssertEqual(aStruct->bitfield.getGender(), GenderEnum::FEMALE);
    XCTAssertEqual(aStruct->bitfield.getParty(),  PartyEnum::CONSERVATIVE);
    XCTAssertEqual(aStruct->bitfield.getNo(),     NoEnum::no);

}

- (void)testStruct46 {
    auto aStruct = (testStruct46*)memblockFromPath(genDir+"/testStruct46.bin");
    XCTAssertEqual(aStruct->bitfield.getA(), 0);
    XCTAssertEqual(aStruct->bitfield.getB(), 0);
    XCTAssertEqual(aStruct->bitfield.getC(), 0);
    XCTAssertEqual(aStruct->bitfield.getD(), 0);
    
    aStruct->bitfield.setB(-8);
    XCTAssertEqual(aStruct->bitfield.getA(), 0);
    XCTAssertEqual(aStruct->bitfield.getB(), -8);
    XCTAssertEqual(aStruct->bitfield.getC(), 0);
    XCTAssertEqual(aStruct->bitfield.getD(), 0);

    aStruct->bitfield.setB(7);
    XCTAssertEqual(aStruct->bitfield.getA(), 0);
    XCTAssertEqual(aStruct->bitfield.getB(), 7);
    XCTAssertEqual(aStruct->bitfield.getC(), 0);
    XCTAssertEqual(aStruct->bitfield.getD(), 0);

    aStruct->bitfield.setB(0);
    XCTAssertEqual(aStruct->bitfield.getA(), 0);
    XCTAssertEqual(aStruct->bitfield.getB(), 0);
    XCTAssertEqual(aStruct->bitfield.getC(), 0);
    XCTAssertEqual(aStruct->bitfield.getD(), 0);

    aStruct->bitfield.setC(15);
    XCTAssertEqual(aStruct->bitfield.getA(), 0);
    XCTAssertEqual(aStruct->bitfield.getB(), 0);
    XCTAssertEqual(aStruct->bitfield.getC(), 15);
    XCTAssertEqual(aStruct->bitfield.getD(), 0);

    aStruct->bitfield.setC(256);
    XCTAssertEqual(aStruct->bitfield.getA(), 0);
    XCTAssertEqual(aStruct->bitfield.getB(), 0);
    XCTAssertEqual(aStruct->bitfield.getC(), 0);
    XCTAssertEqual(aStruct->bitfield.getD(), 0);

    aStruct->bitfield.setC(0b11111111);
    XCTAssertEqual(aStruct->bitfield.getA(), 0);
    XCTAssertEqual(aStruct->bitfield.getB(), 0);
    XCTAssertEqual(aStruct->bitfield.getC(), 15);
    XCTAssertEqual(aStruct->bitfield.getD(), 0);
    
    aStruct->bitfield.setB(-8);
    aStruct->bitfield.setC(0b11111111);
    aStruct->bitfield.setD(15);
    XCTAssertEqual(aStruct->bitfield.getA(), 0);
    XCTAssertEqual(aStruct->bitfield.getB(), -8);
    XCTAssertEqual(aStruct->bitfield.getC(), 15);
    XCTAssertEqual(aStruct->bitfield.getD(), 15);
    
    aStruct->bitfield.setC(0);
    XCTAssertEqual(aStruct->bitfield.getA(), 0);
    XCTAssertEqual(aStruct->bitfield.getB(), -8);
    XCTAssertEqual(aStruct->bitfield.getC(), 0);
    XCTAssertEqual(aStruct->bitfield.getD(), 15);
}

- (void)testStruct47 {
    auto aStruct = (testStruct47*)memblockFromPath(genDir+"/testStruct47.bin");
    XCTAssertEqual(aStruct->bitfield.getNumber(), 0);
    
    aStruct->bitfield.setNumber(-1);
    XCTAssertEqual(aStruct->bitfield.getNumber(),-1);

    aStruct->bitfield.setNumber(1);
    XCTAssertEqual(aStruct->bitfield.getNumber(), 1);
    
    aStruct->bitfield.setNumber(0x7fff);
    XCTAssertEqual(aStruct->bitfield.getNumber(), 0x7fff);

    aStruct->bitfield.setNumber(-0x8000);
    XCTAssertEqual(aStruct->bitfield.getNumber(), -0x8000);
    
    aStruct->bitfield.setNumber(0x7fffffff);
    XCTAssertEqual(aStruct->bitfield.getNumber(), 0x7fffffff);
    
    aStruct->bitfield.setNumber(-0x80000000);
    XCTAssertEqual(aStruct->bitfield.getNumber(), -0x80000000);
}


@end








