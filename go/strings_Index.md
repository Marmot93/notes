# [一起读源码] strings.Index

# stings.Index
```go
// 返回 s 中 substr 第一个实例的索引，如果 substr 不存在于 s 中，则返回 -1。
func Index(s, substr string) int {
    // 前面关于 strings.Count 中我们提到过 len 和 utf8.RuneCountInString 有区别
    // ASCII 字符串长度使用 len
    // Unicode 字符串长度使用 utf8.RuneCountInString
    // 下面主要使用了 strings.IndexByte，底层是 bytealg.IndexByteString
    // bytealg.IndexByteString 是用的汇编操作寄存器，为 ASCII 编码
    // 所以这里使用的 len 来计算 substr 的长度
	n := len(substr)
	switch {
	case n == 0:
		return 0
	case n == 1:
		return IndexByte(s, substr[0])
	case n == len(s):
		if substr == s {
			return 0
		}
		return -1
	case n > len(s):
		return -1
	case n <= bytealg.MaxLen:
		// Use brute force when s and substr both are small
		if len(s) <= bytealg.MaxBruteForce {
			return bytealg.IndexString(s, substr)
		}
		c0 := substr[0]
		c1 := substr[1]
		i := 0
		t := len(s) - n + 1
		fails := 0
		for i < t {
			if s[i] != c0 {
				// IndexByte is faster than bytealg.IndexString, so use it as long as
				// we're not getting lots of false positives.
				o := IndexByte(s[i+1:t], c0)
				if o < 0 {
					return -1
				}
				i += o + 1
			}
			if s[i+1] == c1 && s[i:i+n] == substr {
				return i
			}
			fails++
			i++
			// Switch to bytealg.IndexString when IndexByte produces too many false positives.
			if fails > bytealg.Cutover(i) {
				r := bytealg.IndexString(s[i:], substr)
				if r >= 0 {
					return r + i
				}
				return -1
			}
		}
		return -1
	}
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
		if fails >= 4+i>>4 && i < t {
			// See comment in ../bytes/bytes.go.
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