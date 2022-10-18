package disk

import (
	"fmt"
	"io/ioutil"
	"os"
)

// CreateWithContent
// @Description:
// @Parameter dir
// @Parameter prefix
// @Parameter suffix
// @Parameter content
// @return fileName
// @return err
func CreateWithContent(dir, prefix, suffix string, content []byte) (fileName string, err error) {
	file, err := ioutil.TempFile(dir, fmt.Sprintf("%s-*.%s", prefix, suffix))
	if err != nil {
		err = fmt.Errorf("fail to create temp file err: %v", err)
		return "", err
	}
	fileName = file.Name()
	var ct int
	ct, err = file.Write(content)
	if err != nil || ct != len(content) {
		file.Close()
		os.Remove(fileName)
		err = fmt.Errorf("fail to write content to temp file %s, err: %v, length of content: %d, writed: %d", fileName, err, len(content), ct)
		return "", err
	}
	if err := file.Close(); err != nil {
		panic(fmt.Sprintln("fail to close temp file ", fileName))
	}
	return fileName, nil
}

func ReadFileContent(path string) (content string, err error) {
	data, err := ioutil.ReadFile(path)
	if err != nil {
		return
	}
	return string(data), nil
}
