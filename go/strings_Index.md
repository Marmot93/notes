# [一起读源码] strings.Index 精巧而不迂腐
- [stings.Index解析](#stingsindex解析)
- [额外内容](#额外内容)
  - [关于 bytealg.Cutover](#关于-bytealgcutover)
  - [关于IndexPeriodic这部分的测试](#关于indexperiodic这部分的测试)
  - [关于IndexByte is faster than bytealg.IndexString](#关于indexbyte-is-faster-than-bytealgindexstring)
- [总结](#总结)

## stings.Index解析
```go
// 返回 s 中 substr 第一个实例的索引，如果 substr 不存在于 s 中，则返回 -1。
func Index(s, substr string) int {
    // 前面在 strings.Count 中我们提到过 len 和 utf8.RuneCountInString 有区别
    // 表示 ASCII 字符串长度使用 len
    // 表示 Unicode 字符串长度使用 utf8.RuneCountInString
    // 下面主要使用了 strings.IndexByte，底层是 bytealg.IndexByteString
    // bytealg.IndexByteString 是用的汇编，在寄存器中操作是ASCII编码
    // 所以这里使用的 len 来计算 substr 的长度
    n := len(substr)
    // 根据 len(substr) 处理不不同的 case
	switch {
    // 这个没啥好说的
	case n == 0:
        return 0
    // 只有一个字节的时候，使用的 bytealg.IndexByteString
	case n == 1:
        return IndexByte(s, substr[0])
    // 同长度直接比较相等
	case n == len(s):
		if substr == s {
			return 0
		}
        return -1
    // 子串更长没什么好说的
	case n > len(s):
        return -1
    // 这里根据 n 和 MaxLen 对比来决定是否暴力求解
    // MaxLen 在 不同架构中有不同的值
    // 参见 internal/cpu/index_[对应平台].go 中的 init()
	case n <= bytealg.MaxLen:
        // Use brute force when s and substr both are small
        // 当子串小于 MaxLen，且模式串小于 MaxBruteForce(固定值64)的时候
        // 使用 bytealg.IndexString暴力求解
		if len(s) <= bytealg.MaxBruteForce {
			return bytealg.IndexString(s, substr)
        }
        // 子串小，模式串大的时候
        // 子串的第一二个字符
		c0 := substr[0]
		c1 := substr[1]
        i := 0
        // 最长需要移动的距离就是 t = len(s) - n + 1
        t := len(s) - n + 1
        // 这个是记录偷懒失败次数的，必须夸一下go的设计：精巧而不迂腐
        fails := 0
        // 迭代主串来比较子串
        // i:当前索引，t：最大索引
		for i < t {
            // 主串的第i个 != c0
			if s[i] != c0 {
				// IndexByte is faster than bytealg.IndexString, so use it as long as
                // we're not getting lots of false positives.
                // 这里官方给出了解释，因为 IndexByte is faster than bytealg.IndexString
                o := IndexByte(s[i+1:t], c0)
                // 从i到t都没有找到c0，那就肯定没有
				if o < 0 {
					return -1
                }
                // 如果找到了，直接移动i到匹配到c0后一个索引
				i += o + 1
            }
            // 这里其实非常的偷懒，懒是优化代码的第一动力
            // 当c0,c1能呼应上的时候，直接拉后面的来求等于，好家伙！
            // 可能这也是go性能好的原因之一，写代码有时候不要过于迂腐！！
			if s[i+1] == c1 && s[i:i+n] == substr {
				return i
            }
            // 偷懒失败+1
            fails++
            // 检索的索引后移一位
			i++
            // Switch to bytealg.IndexString when IndexByte produces too many false positives.
            // 走到这里，代表这个懒实在是偷不下去了
            // 关于容忍失败的最大次数 bytealg.Cutover = (i + 16) / 8
            // 关于bytealg.Cutover在bytes.Index注释中也有讲解，这个问题放在文章的后面
			if fails > bytealg.Cutover(i) {
                // 还记得到这里的前提条件么？
                // 当子串小于 MaxLen，模式串小于 MaxBruteForce(固定值64)的时候
                // 这个时候直接往寄存器里面吃，也快于 Rabin-Karp
                r := bytealg.IndexString(s[i:], substr)
                // 找到了
				if r >= 0 {
					return r + i
                }
                // 没找到
				return -1
			}
        }
        // 迭代完了都没找到
		return -1
    }
    // 到这里其实就是 default: 模式串和子串都比较大
    // 没办法暴力求解了，被迫干活
    // 这里都参考上面 case n <= bytealg.MaxLen 不再赘述
	c0 := substr[0]
	c1 := substr[1]
	i := 0
	t := len(s) - n + 1
	fails := 0
	for i < t {
		if s[i] != c0 {
			o := IndexByte(s[i+1:t], c0)
			if o < 0 {
				return -1
			}
			i += o + 1
		}
		if s[i+1] == c1 && s[i:i+n] == substr {
			return i
		}
		i++
        fails++
        // 最大容忍次数为 (4+i>>4) == (4+i/16)
        // 这里 增加了 i < t 条件是因为上面的 i++
        // 可以让最后一次循环的时候不再浪费时间执行上面的代码块
		if fails >= 4+i>>4 && i < t {
            // See comment in ../bytes/bytes.go.
            // TODD：好家伙又是一个坑 RabinKarp 
            // 那下次读这个的源码吧，大体思路是：
            // 对模式串和文本中的子串分别进行哈希运算，以便对它们进行快速比对
			j := bytealg.IndexRabinKarp(s[i:], substr)
			if j < 0 {
				return -1
			}
			return i + j
		}
	}
	return -1
}
```
---
## 额外内容

### 关于 bytealg.Cutover
```
// Give up on IndexByte, it isn't skipping ahead
// far enough to be better than Rabin-Karp.
// Experiments (using IndexPeriodic) suggest
// the cutover is about 16 byte skips.
// TODO: if large prefixes of sep are matching
// we should cutover at even larger average skips,
// because Equal becomes that much more expensive.
// This code does not take that effect into account.
```
大概意思就是：  
前面已经比较过 i 个了，还是失败，这个时候用暴力求等的成本就大于 `RabinKarp`的求解成本了  
由`IndexPeriodic`得出的跳跃字节数是16，所以才这么干的

----

### 关于IndexPeriodic这部分的测试
在 `strings.strings_test.BenchmarkIndexPeriodic`  
代码放下面可以写一个 `main_test.go`放进去跑跑看看
```go
package main

import (
	"fmt"
	"strings"
	"testing"
)

func BenchmarkIndexPeriodic(b *testing.B) {
	key := "aa"
	for _, skip := range [...]int{2, 4, 8, 16, 32, 64} {
		b.Run(fmt.Sprintf("IndexPeriodic%d", skip), func(b *testing.B) {
			s := strings.Repeat("a"+strings.Repeat(" ", skip-1), 1<<16/skip)
			for i := 0; i < b.N; i++ {
				strings.Index(s, key)
			}
		})
	}
}
```

----

### 关于IndexByte is faster than bytealg.IndexString
以最常见的`amd64`的架构为例子

```x86asm
// IndexByte 调用的汇编是 IndexByteString
TEXT    ·IndexByteString(SB), NOSPLIT, $0-32
	MOVQ s_base+0(FP), SI
	MOVQ s_len+8(FP), BX
	MOVB c+16(FP), AL
	LEAQ ret+24(FP), R8
	JMP  indexbytebody<>(SB)
```
---

```x86asm
TEXT ·IndexString(SB),NOSPLIT,$0-40
	MOVQ a_base+0(FP), DI
	MOVQ a_len+8(FP), DX
	MOVQ b_base+16(FP), R8
	MOVQ b_len+24(FP), AX
	MOVQ DI, R10
	LEAQ ret+32(FP), R11
	JMP  indexbody<>(SB)
```

`indexbytebody `也是快于 `indexbody`的，执行步骤大约要少一半

---

## 总结
`精巧而不迂腐`，这也是就是go的魅力和性能所在吧
