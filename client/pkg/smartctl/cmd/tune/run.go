package tune

import (
	"encoding/json"
	"errors"
	"fmt"
	"github.com/smart-inner/smarttune/collector"
	"github.com/smart-inner/smarttune/pkg/genericclioptions"
	"github.com/smart-inner/smarttune/util"
	"github.com/smart-inner/smarttune/util/http"
	"github.com/spf13/cobra"
	"io/ioutil"
	"strings"
	"time"
)

type RunOptions struct {
	Backend string
	MaxIter int32
	Url     string
	Tools   string

	genericclioptions.IOStreams
}

func NewRunOptions(streams genericclioptions.IOStreams) *RunOptions {
	return &RunOptions{
		IOStreams: streams,
	}
}

func NewCmdRun(streams genericclioptions.IOStreams) *cobra.Command {
	o := NewRunOptions(streams)
	cmd := &cobra.Command{
		Use:   "run SESSION_NAME --backend=backend --url=url [--max_iter=max_iter] [--tools=tools]",
		Short: "Start to tune the specified system",
		Long:  `Start to tune the specified system based on the created session`,
		Run: func(cmd *cobra.Command, args []string) {
			util.CheckErr(o.Run(args))
		},
	}

	addRunFlags(cmd, o)

	return cmd
}

func addRunFlags(cmd *cobra.Command, opt *RunOptions) {
	cmd.Flags().StringVar(&opt.Backend, "backend", "", "The backend url for smarttune, such as '127.0.0.1:5000'")
	cmd.Flags().Int32Var(&opt.MaxIter, "max_iter", 1, "The max iteration for algorithm")
	cmd.Flags().StringVar(&opt.Url, "url", "", "The url for accessing target system")
	cmd.Flags().StringVar(&opt.Tools, "tools", "", "The tools for updating system's configuration")
}

func (o *RunOptions) Loop(iter int, arg string) error {
	c := &collector.TiDBCollector{Url: o.Url}
	fmt.Fprintf(o.Out, "Start to collect knobs\n")
	knobs, err := c.CollectKnobs()
	if err != nil {
		return err
	}

	fmt.Fprintf(o.Out, "Start the first collection for metrics\n")
	beforeMetrics, err := c.CollectMetrics()
	if err != nil {
		return err
	}
	startTime := time.Now().UnixMilli()
	time.Sleep(10 * time.Second)
	endTime := time.Now().UnixMilli()

	fmt.Fprintf(o.Out, "Start the second collection for metrics\n")
	afterMetrics, err := c.CollectMetrics()
	if err != nil {
		return err
	}
	summary := make(map[string]interface{})
	summary["start_time"] = startTime
	summary["end_time"] = endTime
	summary["observation_time"] = 10
	summary["system_type"] = "TiDB"
	summary["version"] = "v6.1.0"
	summary["workload"] = "tpcc"
	summaryStr, err := json.Marshal(summary)
	if err != nil {
		return err
	}
	request := make(map[string]interface{})
	request["summary"] = string(summaryStr)
	request["knobs"] = knobs
	request["metrics_before"] = beforeMetrics
	request["metrics_after"] = afterMetrics
	url := fmt.Sprintf("http://%s/api/result/generate/%s", o.Backend, arg)
	headers := make(map[string]string)
	resp, err := http.PostJSON(url, request, headers)
	if err != nil {
		return err
	}
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return err
	}
	var build strings.Builder
	build.WriteString(string(body))
	build.WriteString("\n")
	if resp.StatusCode != 200 {
		fmt.Fprintf(o.ErrOut, build.String())
	}
	fmt.Fprintf(o.Out, build.String())

	url = fmt.Sprintf("http://%s/api/result/query/%s", o.Backend, arg)
	getRequest := make(map[string]string)
	resp, err = http.Get(url, getRequest, headers)
	if err != nil {
		return err
	}
	body, err = ioutil.ReadAll(resp.Body)
	if err != nil {
		return err
	}
	fmt.Println(string(body))

	return nil
}

func (o *RunOptions) Run(args []string) error {
	if len(args) != 1 || len(o.Backend) == 0 || len(o.Url) == 0 {
		return errors.New(fmt.Sprintf("Error: invalid subcommand "+
			"'smartctl create %s --backend=%s --url=%s'", strings.Join(args, " "), o.Backend, o.Url))
	}
	for i := 0; i < int(o.MaxIter); i++ {
		// system is ready
		fmt.Fprintf(o.Out, "The %d-th Loop Starts / Total Loops %d\n", i+1, o.MaxIter)
		if err := o.Loop(i, args[0]); err != nil {
			return err
		}
		fmt.Fprintf(o.Out, "The %d-th Loop Ends / Total Loops %d\n", i+1, o.MaxIter)
	}
	return nil
}
