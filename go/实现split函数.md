# [一起读源码] 关于split的设计

既然这个专题是因为`split`开始的，那就也从`split`开始吧

## strings.Split

查看源码我们可以发现 `strings.Split` 和 `strings.SplitN` 都是套壳的 `strings.genSplit` 这里就直接关注 `strings.genSplit`了

## strings.genSplit
```go
// s：待分割字符串
// sep：子串，
// sepSave：在子数组中包含sepSave字节， 
// n：拆分完成子数组的最大长度
// 关于 n 的分割在 SplitN 的注释中有说明：
//  n > 0: 最多 n 个子串； 最后一个子串将是未拆分的余数。
//  n == 0：结果为零（零子串）
//  n < 0：所有子串
func genSplit(s, sep string, sepSave, n int) []string {
    // n == 0：结果为零（零子串）
	if n == 0 {
		return nil
    }
    // 当 sep == "" 的时候，直接使用 explode
    // explode 将 s 拆分为一段 UTF-8 字符串，
    // 每个 Unicode 字符一个字符串，最多为 n（n < 0 表示没有限制）。
	if sep == "" {
		return explode(s, n)
    }
    // n < 0：所有子串，这里使用了 strings.Count 来计算真实的n值，以及需要准备多大的cap
    // 在下面我们再解析 strings.Count
    // string.Count的主体和下面的for循环及其相似，其核心是 strings.Index
	if n < 0 {
		n = Count(s, sep) + 1
    }
    // 用来存结果的数组
    a := make([]string, n)
    // 因为 n==0 和 n<0 的情况，在上面已经全部处理掉了
    // 所以这里直接 n-- 了，减少一个赋值
    // 从这里往下的 n 就代表需要切几刀了
	n--
	i := 0
	for i < n {
        // 这里还是调用的 strings.Index 
        // 返回值 m 代表第一个复合条件的子串的索引
        m := Index(s, sep)
		if m < 0 {
            // m < 0 (其实就是 -1) 代表没找到符合调节的，直接跳出循环
            // 这里的结果其实就是 a[0] = s
			break
        }
        // 截取切割出来的子串加上sepSave字节，放入 a 
        a[i] = s[:m+sepSave]
        // 切割 s 进入下一个循环
		s = s[m+len(sep):]
		i++
    }
    // 剩余字符串的全放进去
    a[i] = s
    // 这里只剩下一个问题了，为什么返回的是 a[:i+1]，返回 i 个，没有用 n？
    // 因为 n是拆分完成子数组的最大长度, n > i，有可能切不出来 n 个
	return a[:i+1]
}
```
总结:优秀的边界条件处理，尽可能少的内存使用，歪瑞优秀的源码（我似乎在说废话）

## strings.Count
```go
// Count counts the number of non-overlapping instances of substr in s.
// If substr is an empty string, Count returns 1 + the number of Unicode code points in s.
func Count(s, substr string) int {
    // special case
    // 在注释中有说明：当 substr 为空字符串的时候，返回 1 + Unicode字节数
	if len(substr) == 0 {
        // TODO: 这里其实有牵涉 len 和 utf8.RuneCountInString 的区别，留坑
        // 至于这里为什么要 utf8.RuneCountInString(s) + 1
        // 在 https://pkg.go.dev/strings#Count 的 Example中有写明为 before & after each rune
        // 如果有其他想法的欢迎留言交流
		return utf8.RuneCountInString(s) + 1
    }
    // substr 是单个字符的时候用 bytealg.CountString 
    // bytealg.CountString 这个是调用的汇编了
    // 在源码的同目录，不同平台的.s文件中有对应cpu架构的的汇编
    // 汇编这个坑太大，我这里实在填不动了，有兴趣的可以了解一下😂
	if len(substr) == 1 {
		return bytealg.CountString(s, substr[0])
	}
	n := 0
	for {
        // TODO：这里在上面提过，使用了 strings.Index 
        // strings.Index 的除了边界处理以外
        // 主要是根据寄存器的情况情况使用暴力求解或者Rabin-Karp算法
        // 挖个大坑，待填
        i := Index(s, substr)
        // 没找到返回计数
		if i == -1 {
			return n
        }
        // 找到了计数+1
        n++
        // 切出剩余待查字符串
		s = s[i+len(substr):]
	}
}
```
总结：
1. 主题和 genSplit 当中的 for 循环其实是类似的
2. 挖两个坑 `bytealg.CountString`和`strings.Index`


---

剩下的坑下次填了，今天先到这里吧。
